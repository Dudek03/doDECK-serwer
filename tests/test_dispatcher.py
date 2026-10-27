import unittest
from unittest.mock import MagicMock, patch
import json
from flask import Flask
from flask_socketio import SocketIO
from modules.dispatcher import (
    dispatcher_bp,
    execute_command,
    register_dispatcher_events,
)


class TestDispatcher(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.app.register_blueprint(dispatcher_bp, url_prefix="/dispatcher")
        self.client = self.app.test_client()

    @patch("keyboard.send")
    def test_execute_hotkey(self, mock_send):
        success, msg = execute_command("hotkey", "win+d")
        self.assertTrue(success)
        mock_send.assert_called_with("win+d")

    @patch("keyboard.write")
    def test_execute_write(self, mock_write):
        success, msg = execute_command("write", "hello world")
        self.assertTrue(success)
        mock_write.assert_called_with("hello world", exact=True)
        self.assertIn("hello world", msg)

    @patch("webbrowser.open")
    def test_execute_open_url(self, mock_open):
        success, msg = execute_command("open_url", "https://google.com")
        self.assertTrue(success)
        mock_open.assert_called_with("https://google.com")

    def test_execute_open_url_disallowed_scheme(self):
        success, msg = execute_command("open_url", "javascript:alert(1)")
        self.assertFalse(success)
        self.assertIn("Niepoprawny URL", msg)

    @patch("pygetwindow.getWindowsWithTitle")
    @patch("os.startfile")
    @patch("time.sleep")
    def test_execute_workspace(self, mock_sleep, mock_startfile, mock_get_windows):
        mock_win = MagicMock()
        mock_win.isMinimized = False
        mock_get_windows.side_effect = [[mock_win]]

        target = [
            {
                "title": "Test Window",
                "x": 10,
                "y": 10,
                "width": 500,
                "height": 500,
                "exec_path": "C:\\test.exe",
            }
        ]

        success, msg = execute_command("workspace", target)
        self.assertTrue(success)
        mock_win.moveTo.assert_called_with(10, 10)
        mock_win.resizeTo.assert_called_with(500, 500)
        mock_win.activate.assert_called_once()

    def test_execute_unknown_command(self):
        success, msg = execute_command("invalid_cmd", "")
        self.assertFalse(success)
        self.assertIn("Nieznana komenda", msg)

    @patch("keyboard.send")
    def test_execute_command_exception(self, mock_send):
        mock_send.side_effect = RuntimeError("Keyboard failure")
        success, msg = execute_command("hotkey", "ctrl+alt+del")
        self.assertFalse(success)
        self.assertIn("Keyboard failure", msg)

    @patch("os.path.exists")
    @patch("builtins.open")
    def test_get_layout_existing(self, mock_open, mock_exists):
        mock_exists.return_value = True
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = json.dumps(
            {"active_layout_id": "test", "layouts": []}
        )
        mock_open.return_value = mock_file

        with patch("json.load", return_value={"active_layout_id": "test", "layouts": []}):
            response = self.client.get("/dispatcher/get_layout")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()["active_layout_id"], "test")

    @patch("os.path.exists", return_value=False)
    @patch("builtins.open")
    def test_get_layout_default_created(self, mock_open, mock_exists):
        response = self.client.get("/dispatcher/get_layout")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("active_layout_id", data)
        self.assertIn("layouts", data)

    @patch("builtins.open")
    def test_save_layout_success(self, mock_open):
        new_layout = {"active_layout_id": "custom", "layouts": []}
        response = self.client.post("/dispatcher/save_layout", json=new_layout)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    @patch("modules.dispatcher.gw.getAllWindows")
    def test_scan_windows(self, mock_get_all):
        win1 = MagicMock()
        win1.title = "App 1"
        win1.visible = True
        win1.width = 800
        win1.height = 600
        win1.left = 100
        win1.top = 100
        win1._hWnd = 12345

        win2 = MagicMock()
        win2.title = ""  # Empty title should be skipped
        win2.visible = True

        mock_get_all.return_value = [win1, win2]

        response = self.client.get("/dispatcher/scan_windows")
        self.assertEqual(response.status_code, 200)
        windows = response.get_json()["windows"]
        self.assertEqual(len(windows), 1)
        self.assertEqual(windows[0]["title"], "App 1")

    @patch("modules.dispatcher.get_or_create_secret", return_value="secret123")
    @patch("modules.dispatcher.get_local_ip", return_value="192.168.1.50")
    def test_get_pairing_data_localhost(self, mock_ip, mock_secret):
        response = self.client.get(
            "/dispatcher/get_pairing_data",
            environ_base={"REMOTE_ADDR": "127.0.0.1"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["ip"], "192.168.1.50")
        self.assertEqual(data["secret"], "secret123")

    def test_get_pairing_data_forbidden(self):
        response = self.client.get(
            "/dispatcher/get_pairing_data",
            environ_base={"REMOTE_ADDR": "192.168.1.100"},
        )
        self.assertEqual(response.status_code, 403)

    @patch("modules.dispatcher.execute_command")
    def test_trigger_action_rest_success(self, mock_exec):
        mock_exec.return_value = (True, "Done")
        response = self.client.post(
            "/dispatcher/trigger",
            json={"command": "hotkey", "args": "ctrl+c"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    @patch("modules.dispatcher.execute_command")
    def test_trigger_action_rest_fail(self, mock_exec):
        mock_exec.return_value = (False, "Command failed")
        response = self.client.post(
            "/dispatcher/trigger",
            json={"command": "invalid", "args": ""},
        )
        self.assertEqual(response.status_code, 400)

    def test_save_layout_remote_forbidden(self):
        response = self.client.post(
            "/dispatcher/save_layout",
            json={"layouts": []},
            environ_base={"REMOTE_ADDR": "192.168.1.100"},
        )
        self.assertEqual(response.status_code, 403)

    def test_save_layout_invalid_format(self):
        response = self.client.post(
            "/dispatcher/save_layout",
            json="invalid_not_a_dict",
        )
        self.assertEqual(response.status_code, 400)

    def test_scan_windows_remote_forbidden(self):
        response = self.client.get(
            "/dispatcher/scan_windows",
            environ_base={"REMOTE_ADDR": "192.168.1.100"},
        )
        self.assertEqual(response.status_code, 403)

    def test_trigger_action_rest_remote_without_secret_forbidden(self):
        response = self.client.post(
            "/dispatcher/trigger",
            json={"command": "hotkey", "args": "win+d"},
            environ_base={"REMOTE_ADDR": "192.168.1.100"},
        )
        self.assertEqual(response.status_code, 403)

    @patch("modules.dispatcher.get_or_create_secret", return_value="super_secret_key")
    @patch("modules.dispatcher.execute_command")
    def test_trigger_action_rest_remote_with_valid_secret(
        self, mock_exec, mock_secret
    ):
        mock_exec.return_value = (True, "Executed via secret")
        response = self.client.post(
            "/dispatcher/trigger",
            json={"command": "hotkey", "args": "win+d"},
            headers={"X-DoDeck-Secret": "super_secret_key"},
            environ_base={"REMOTE_ADDR": "192.168.1.100"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")


class TestDispatcherSocketEvents(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        register_dispatcher_events(self.socketio)
        self.client = self.socketio.test_client(self.app)

    @patch("modules.dispatcher.verify_socket_payload", return_value=True)
    @patch("modules.dispatcher.execute_command")
    def test_trigger_action_socket_valid_hmac(self, mock_exec, mock_verify):
        mock_exec.return_value = (True, "Hotkey executed")
        self.client.emit(
            "trigger_action",
            {"command": "hotkey", "args": "win+d", "signature": "abc", "timestamp": "123"},
        )
        mock_exec.assert_called_once_with("hotkey", "win+d")

    @patch("modules.dispatcher.verify_socket_payload", return_value=False)
    @patch("modules.dispatcher.execute_command")
    def test_trigger_action_socket_invalid_hmac(self, mock_exec, mock_verify):
        self.client.emit(
            "trigger_action",
            {"command": "hotkey", "args": "win+d", "signature": "bad", "timestamp": "123"},
        )
        mock_exec.assert_not_called()

    @patch("modules.dispatcher.verify_socket_payload", return_value=True)
    @patch("modules.dispatcher.execute_command")
    def test_trigger_macro_socket(self, mock_exec, mock_verify):
        mock_exec.return_value = (True, "Step executed")
        steps = [
            {"command": "hotkey", "args": "win+r", "delay": 0},
            {"command": "write", "args": "notepad", "delay": 0},
        ]
        self.client.emit("trigger_macro", {"steps": steps})
        self.assertEqual(mock_exec.call_count, 2)


if __name__ == "__main__":
    unittest.main()
