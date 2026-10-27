import unittest
from unittest.mock import MagicMock, patch
from flask import Flask
from flask_socketio import SocketIO
from modules.audio import (
    audio_bp,
    get_session_audio_data,
    register_audio_events,
)


class TestAudio(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.app.register_blueprint(audio_bp, url_prefix="/audio")
        self.client = self.app.test_client()

    @patch("modules.audio.AudioUtilities")
    def test_get_session_audio_data_success(self, mock_utils):
        mock_session = MagicMock()
        mock_session.Process.name.return_value = "TestApp"

        mock_volume = MagicMock()
        mock_volume.GetMasterVolume.return_value = 0.75
        mock_volume.GetMute.return_value = 0
        mock_session._ctl.QueryInterface.return_value = mock_volume

        result = get_session_audio_data(mock_session)

        self.assertIsNotNone(result)
        self.assertEqual(result["App"], "TestApp")
        self.assertEqual(result["Volume"], 75)
        self.assertEqual(result["isMuted"], 0)

    def test_get_session_audio_data_no_process(self):
        mock_session = MagicMock()
        mock_session.Process = None

        result = get_session_audio_data(mock_session)
        self.assertIsNone(result)

    @patch("modules.audio.AudioUtilities")
    def test_get_session_audio_data_muted(self, mock_utils):
        mock_session = MagicMock()
        mock_session.Process.name.return_value = "MutedApp"

        mock_volume = MagicMock()
        mock_volume.GetMasterVolume.return_value = 0.5
        mock_volume.GetMute.return_value = 1  # Muted

        mock_session._ctl.QueryInterface.return_value = mock_volume

        result = get_session_audio_data(mock_session)
        self.assertIsNone(result)

    def test_get_session_audio_data_exception(self):
        mock_session = MagicMock()
        mock_session.Process.name.side_effect = Exception("COM error")

        result = get_session_audio_data(mock_session)
        self.assertIsNone(result)

    @patch("modules.audio.comtypes.CoInitialize")
    @patch("modules.audio.AudioUtilities.GetAllSessions")
    def test_get_apps_volume_endpoint(self, mock_sessions, mock_coinit):
        mock_session = MagicMock()
        mock_session.Process.name.return_value = "Spotify.exe"
        mock_volume = MagicMock()
        mock_volume.GetMasterVolume.return_value = 0.5
        mock_volume.GetMute.return_value = 0
        mock_session._ctl.QueryInterface.return_value = mock_volume
        mock_sessions.return_value = [mock_session]

        response = self.client.get("/audio/getAppsVolume")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["ilosc"], 1)
        self.assertEqual(data["aplikacje"][0]["App"], "Spotify.exe")
        self.assertEqual(data["aplikacje"][0]["Volume"], 50)

    @patch("modules.audio.comtypes.CoInitialize")
    @patch("modules.audio.AudioUtilities.GetAllSessions")
    def test_set_app_volume_success(self, mock_sessions, mock_coinit):
        mock_session = MagicMock()
        mock_session.Process.name.return_value = "chrome.exe"
        mock_volume = MagicMock()
        mock_session._ctl.QueryInterface.return_value = mock_volume
        mock_sessions.return_value = [mock_session]

        response = self.client.post(
            "/audio/setAppVolume",
            json={"app": "chrome.exe", "volume": 80},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "OK")
        mock_volume.SetMasterVolume.assert_called_once_with(0.8, None)

    @patch("modules.audio.comtypes.CoInitialize")
    def test_set_app_volume_missing_data(self, mock_coinit):
        response = self.client.post("/audio/setAppVolume", json={})
        self.assertEqual(response.status_code, 400)

    @patch("modules.audio.comtypes.CoInitialize")
    @patch("modules.audio.AudioUtilities.GetAllSessions")
    def test_set_app_volume_not_found(self, mock_sessions, mock_coinit):
        mock_sessions.return_value = []
        response = self.client.post(
            "/audio/setAppVolume",
            json={"app": "nonexistent.exe", "volume": 50},
        )
        self.assertEqual(response.status_code, 404)

    @patch("modules.audio.comtypes.CoInitialize")
    @patch("modules.audio.AudioUtilities.GetSpeakers")
    def test_mute_all_apps_endpoint(self, mock_speakers, mock_coinit):
        mock_device = MagicMock()
        mock_endpoint = MagicMock()
        mock_endpoint.GetMute.return_value = False
        mock_device.Activate.return_value.QueryInterface.return_value = mock_endpoint
        mock_speakers.return_value = mock_device

        response = self.client.get("/audio/muteAllApps")
        self.assertEqual(response.status_code, 200)
        mock_endpoint.SetMute.assert_called_once_with(True, None)

    @patch("modules.audio.win32gui.GetForegroundWindow")
    @patch("modules.audio.win32api.SendMessage")
    def test_mic3_endpoint(self, mock_send, mock_get_window):
        mock_get_window.return_value = 12345
        response = self.client.get("/audio/mic3")
        self.assertEqual(response.status_code, 200)
        mock_send.assert_called_once()


class TestAudioSocketEvents(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        register_audio_events(self.socketio)
        self.client = self.socketio.test_client(self.app)

    @patch("modules.audio.comtypes.CoInitialize")
    @patch("modules.audio.AudioUtilities.GetAllSessions")
    def test_socket_get_audio_volume(self, mock_sessions, mock_coinit):
        mock_session = MagicMock()
        mock_session.Process.name.return_value = "Discord.exe"
        mock_volume = MagicMock()
        mock_volume.GetMasterVolume.return_value = 0.6
        mock_volume.GetMute.return_value = 0
        mock_session._ctl.QueryInterface.return_value = mock_volume
        mock_sessions.return_value = [mock_session]

        self.client.emit("get_audio_volume")
        received = self.client.get_received()
        events = [r for r in received if r["name"] == "audio_volume_data"]
        self.assertTrue(len(events) > 0)
        self.assertEqual(events[0]["args"][0]["ilosc"], 1)

    @patch("modules.audio.comtypes.CoInitialize")
    @patch("modules.audio.AudioUtilities.GetAllSessions")
    def test_socket_set_audio_volume(self, mock_sessions, mock_coinit):
        mock_session = MagicMock()
        mock_session.Process.name.return_value = "Game.exe"
        mock_volume = MagicMock()
        mock_session._ctl.QueryInterface.return_value = mock_volume
        mock_sessions.return_value = [mock_session]

        self.client.emit("set_audio_volume", {"app": "Game.exe", "volume": 40})
        mock_volume.SetMasterVolume.assert_called_once_with(0.4, None)

    @patch("modules.audio.comtypes.CoInitialize")
    @patch("modules.audio.AudioUtilities.GetSpeakers")
    def test_socket_toggle_mute_all(self, mock_speakers, mock_coinit):
        mock_device = MagicMock()
        mock_endpoint = MagicMock()
        mock_endpoint.GetMute.return_value = True
        mock_device.Activate.return_value.QueryInterface.return_value = mock_endpoint
        mock_speakers.return_value = mock_device

        self.client.emit("toggle_mute_all")
        mock_endpoint.SetMute.assert_called_once_with(False, None)

    @patch("modules.audio.win32gui.GetForegroundWindow")
    @patch("modules.audio.win32api.SendMessage")
    def test_socket_toggle_mic(self, mock_send, mock_get_window):
        mock_get_window.return_value = 9999
        self.client.emit("toggle_mic_mute")
        mock_send.assert_called_once()


if __name__ == "__main__":
    unittest.main()
