import unittest
from unittest.mock import patch
import os
import sys
from modules.paths import (
    get_app_data_dir,
    get_config_path,
    set_safe_working_directory,
)


class TestPaths(unittest.TestCase):
    def test_get_app_data_dir_creates_dir(self):
        data_dir = get_app_data_dir()
        self.assertTrue(os.path.exists(data_dir))
        self.assertTrue(data_dir.endswith("doDECK"))

    def test_get_config_path_local_exists(self):
        # W repozytorium buttons_config.json istnieje w cwd
        path = get_config_path("buttons_config.json")
        self.assertTrue(os.path.isabs(path) or os.path.exists(path))

    @patch("os.getcwd", return_value=r"C:\Windows\System32")
    def test_get_config_path_ignores_system32(self, mock_getcwd):
        # Gdy cwd to C:\Windows\System32, nie powinno zwracać C:\Windows\System32\buttons_config.json
        path = get_config_path("buttons_config.json")
        self.assertNotIn("System32", path)
        self.assertTrue("doDECK" in path)

    @patch("os.getcwd", return_value=r"C:\Windows\System32")
    @patch("os.chdir")
    def test_set_safe_working_directory_from_system32(self, mock_chdir, mock_getcwd):
        set_safe_working_directory()
        mock_chdir.assert_called_once()
        target = mock_chdir.call_args[0][0]
        self.assertTrue("doDECK" in target)

    @patch("os.getcwd", return_value=r"D:\SafePath")
    @patch("os.chdir")
    def test_set_safe_working_directory_ignores_normal_path(self, mock_chdir, mock_getcwd):
        set_safe_working_directory()
        mock_chdir.assert_not_called()


if __name__ == "__main__":
    unittest.main()
