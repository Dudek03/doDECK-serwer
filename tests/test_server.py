import unittest
from unittest.mock import MagicMock, patch
from serwer import (
    app,
    socketio,
    create_default_icon,
    quit_application,
    open_web_editor,
    start_server,
)


class TestServer(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.socket_client = socketio.test_client(app)

    @patch("serwer.app.send_static_file")
    def test_index_route(self, mock_send_static):
        mock_send_static.return_value = "<html>OK</html>"
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        mock_send_static.assert_called_once_with("index.html")

    @patch("serwer.get_or_create_secret", return_value="test_secret_123")
    @patch("serwer.get_local_ip", return_value="192.168.1.100")
    def test_api_pairing_localhost(self, mock_ip, mock_secret):
        response = self.client.get(
            "/api/pairing", environ_base={"REMOTE_ADDR": "127.0.0.1"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["ip"], "192.168.1.100")
        self.assertEqual(data["port"], 5000)
        self.assertEqual(data["secret"], "test_secret_123")

    def test_api_pairing_forbidden(self):
        response = self.client.get(
            "/api/pairing", environ_base={"REMOTE_ADDR": "192.168.1.55"}
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("Brak uprawnień", response.get_json()["error"])

    def test_create_default_icon(self):
        img = create_default_icon()
        self.assertIsNotNone(img)
        self.assertEqual(img.size, (64, 64))

    @patch("serwer.os._exit")
    def test_quit_application(self, mock_exit):
        mock_icon = MagicMock()
        quit_application(mock_icon, None)
        mock_icon.stop.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch("serwer.webbrowser.open")
    def test_open_web_editor(self, mock_open):
        open_web_editor(None, None)
        mock_open.assert_called_once_with("http://localhost:5000/")

    @patch("serwer.setup_tray_icon")
    @patch("serwer.threading.Thread")
    def test_start_server(self, mock_thread, mock_tray):
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        start_server()

        mock_thread_instance.start.assert_called_once()
        mock_tray.assert_called_once()

    @patch("modules.dispatcher.verify_socket_payload", return_value=True)
    @patch("modules.dispatcher.execute_command")
    def test_trigger_action_socket_integration(self, mock_execute, mock_verify):
        mock_execute.return_value = (True, "Success")
        self.socket_client.emit(
            "trigger_action",
            {"command": "hotkey", "args": "ctrl+c", "signature": "ok", "timestamp": "123"},
        )
        mock_execute.assert_called_once_with("hotkey", "ctrl+c")

    @patch("modules.dispatcher.verify_socket_payload", return_value=True)
    @patch("modules.dispatcher.execute_command")
    def test_trigger_macro_socket_integration(self, mock_execute, mock_verify):
        mock_execute.return_value = (True, "Step ok")
        steps = [
            {"command": "hotkey", "args": "win+r", "delay": 0},
            {"command": "write", "args": "cmd", "delay": 0},
        ]
        self.socket_client.emit("trigger_macro", {"steps": steps})
        self.assertEqual(mock_execute.call_count, 2)


if __name__ == "__main__":
    unittest.main()
