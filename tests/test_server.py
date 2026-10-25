import unittest
from unittest.mock import patch, MagicMock
from app import app, socketio


class TestServerSockets(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.socket_client = socketio.test_client(app)

    @patch("app.execute_command")
    def test_trigger_action_socket(self, mock_execute):
        mock_execute.return_value = (True, "Success")
        self.socket_client.emit(
            "trigger_action", {"command": "hotkey", "args": "ctrl+c"}
        )

        mock_execute.assert_called_once_with("hotkey", "ctrl+c")

    @patch("keyboard.send")
    @patch("keyboard.write")
    @patch("time.sleep")
    def test_trigger_macro_socket(self, mock_sleep, mock_write, mock_send):
        macro_steps = [
            {"command": "hotkey", "args": "win+r", "delay": 100},
            {"command": "write", "args": "cmd", "delay": 0},
        ]
        self.socket_client.emit("trigger_macro", {"steps": macro_steps})

        mock_send.assert_called_once_with("win+r")
        mock_sleep.assert_called_once_with(0.1)
        mock_write.assert_called_once_with("cmd", exact=True)

    @patch("app.get_layout_data")
    def test_get_layout_api(self, mock_get_layout):
        mock_get_layout.return_value = {"active_layout_id": "test", "layouts": []}
        response = self.client.get("/dispatcher/get_layout")

        self.assertEqual(response.status_code, 200)
        self.assertIn("active_layout_id", response.json)


if __name__ == "__main__":
    unittest.main()
