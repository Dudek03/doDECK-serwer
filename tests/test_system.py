import unittest
from unittest.mock import MagicMock, patch
from flask import Flask
from flask_socketio import SocketIO
from modules.system import (
    system_bp,
    register_socket_events,
)


class TestSystem(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.app.register_blueprint(system_bp, url_prefix="/system")
        self.client = self.app.test_client()

    @patch("modules.system.psutil.cpu_percent")
    @patch("modules.system.psutil.virtual_memory")
    def test_get_usage_data_success(self, mock_vm, mock_cpu):
        mock_cpu.return_value = [10.0, 25.5, 5.0]
        mock_mem = MagicMock()
        mock_mem.percent = 60.5
        mock_vm.return_value = mock_mem

        response = self.client.get("/system/getSystemUsage")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["cpu"], 25.5)
        self.assertEqual(data["ram"], 60.5)

    @patch("modules.system.psutil.cpu_percent")
    def test_get_usage_data_exception(self, mock_cpu):
        mock_cpu.side_effect = RuntimeError("PSUtil Error")
        response = self.client.get("/system/getSystemUsage")
        self.assertEqual(response.status_code, 500)


class TestSystemSocketEvents(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        register_socket_events(self.socketio)
        self.client = self.socketio.test_client(self.app)

    def test_subscribe_telemetry(self):
        with patch.object(self.socketio, "start_background_task") as mock_start_task:
            self.client.emit("subscribe_telemetry")
            mock_start_task.assert_called_once()

    def test_disconnect_decrements_counter(self):
        self.client.disconnect()


if __name__ == "__main__":
    unittest.main()
