import unittest
from unittest.mock import MagicMock, patch
from modules.dispatcher import execute_command

class TestDispatcher(unittest.TestCase):
    @patch('keyboard.send')
    def test_execute_hotkey(self, mock_send):
        success, msg = execute_command("hotkey", "win+d")
        self.assertTrue(success)
        mock_send.assert_called_with("win+d")

    @patch('webbrowser.open')
    def test_execute_open_url(self, mock_open):
        success, msg = execute_command("open_url", "https://google.com")
        self.assertTrue(success)
        mock_open.assert_called_with("https://google.com")

    @patch('pygetwindow.getWindowsWithTitle')
    @patch('os.startfile')
    @patch('time.sleep')
    def test_execute_workspace(self, mock_sleep, mock_startfile, mock_get_windows):
        # Mock finding a window
        mock_win = MagicMock()
        mock_win.isMinimized = False
        mock_get_windows.side_effect = [[mock_win]]
        
        target = [{
            "title": "Test Window",
            "x": 10,
            "y": 10,
            "width": 500,
            "height": 500,
            "exec_path": "C:\\test.exe"
        }]

        success, msg = execute_command("workspace", target)
        self.assertTrue(success)
        mock_win.moveTo.assert_called()
        mock_win.resizeTo.assert_called()

    def test_execute_unknown_command(self):
        success, msg = execute_command("invalid_cmd", "")
        self.assertFalse(success)
        self.assertIn("Nieznana komenda", msg)

if __name__ == "__main__":
    unittest.main()
