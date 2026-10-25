import unittest
from unittest.mock import MagicMock, patch
from modules.audio import get_session_audio_data

class TestAudio(unittest.TestCase):
    @patch('modules.audio.AudioUtilities')
    def test_get_session_audio_data_success(self, mock_utils):
        # Mock a successful session
        mock_session = MagicMock()
        mock_session.Process.name.return_value = "TestApp"
        
        # Mock the COM interface
        mock_volume = MagicMock()
        mock_volume.GetMasterVolume.return_value = 0.75
        mock_volume.GetMute.return_value = 0
        
        # Setup the mock structure: session._ctl.QueryInterface(ISimpleAudioVolume)
        # In the code, it's actually: volume = session._ctl.QueryInterface(ISimpleAudioVolume)
        mock_session._ctl.QueryInterface.return_value = mock_volume
        
        result = get_session_audio_data(mock_session)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["App"], "TestApp")
        self.assertEqual(result["Volume"], 75)
        self.assertEqual(result["isMuted"], 0)

    def test_get_session_audio_data_no_process(self):
        mock_session = MagicMock()
        mock_session.Process is None
        
        result = get_session_audio_data(mock_session)
        self.assertIsNone(result)

    @patch('modules.audio.AudioUtilities')
    def test_get_session_audio_data_muted(self, mock_utils):
        mock_session = MagicMock()
        mock_session.Process.name.return_value = "MutedApp"
        
        # Mock a muted volume
        mock_volume = MagicMock()
        mock_volume.GetMasterVolume.return_value = 0.5
        mock_volume.GetMute.return_value = 1 # Muted
        
        mock_session._ctl.QueryInterface.return_value = mock_volume
        
        result = get_session_audio_data(mock_session)
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
