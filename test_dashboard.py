import unittest
import os
import json
import shutil
import tempfile
from unittest.mock import patch, MagicMock

# Import Dashboard
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import dashboard as game_module


class TestCalculinuxDashboard(unittest.TestCase):

    @patch("mmap.mmap")
    @patch("builtins.open")
    def test_initialization(self, mock_open, mock_mmap_cls):
        mock_map = MagicMock()
        mock_mmap_cls.return_value = mock_map
        
        dash = game_module.CalculinuxDashboard()
        self.assertEqual(dash.cursor_r, 0)
        self.assertEqual(dash.cursor_c, 0)
        self.assertEqual(len(dash.grid), 4)
        self.assertEqual(len(dash.grid[0]), 4)
        
        # Verify app mapping exists
        self.assertEqual(dash.grid[0][0]["name"], "Calc")
        self.assertEqual(dash.grid[0][3]["name"], "2048")
        self.assertEqual(dash.grid[2][0]["name"], "mc")

    @patch("mmap.mmap")
    @patch("builtins.open")
    def test_rendering(self, mock_open, mock_mmap_cls):
        mock_map = MagicMock()
        mock_mmap_cls.return_value = mock_map
        
        dash = game_module.CalculinuxDashboard()
        dash.render()
        
        # Verify backbuffer and seek flush execution
        mock_map.seek.assert_called_with(0)
        mock_map.write.assert_called_with(dash.display.backbuffer)

    @patch("subprocess.run")
    @patch("mmap.mmap")
    @patch("builtins.open")
    def test_app_launch(self, mock_open, mock_mmap_cls, mock_run):
        mock_map = MagicMock()
        mock_mmap_cls.return_value = mock_map
        
        dash = game_module.CalculinuxDashboard()
        dash.run_app("Python", "python3")
        
        # Verify subprocess.run was called once with the correct command
        mock_run.assert_called_once_with("python3", shell=True)


if __name__ == "__main__":
    unittest.main()