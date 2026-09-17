import unittest
import os
import json
import shutil
import tempfile
from unittest.mock import patch, MagicMock

# Import Music Player
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import music_player as player_module


class TestMP3Browser(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        # Create some folders and files
        os.makedirs(os.path.join(self.test_dir, "Rock"))
        os.makedirs(os.path.join(self.test_dir, "Pop"))
        with open(os.path.join(self.test_dir, "song1.mp3"), "w") as f:
            f.write("mock mp3 content")
        with open(os.path.join(self.test_dir, "song2.wma"), "w") as f:
            f.write("mock wma content")
        with open(os.path.join(self.test_dir, "readme.txt"), "w") as f:
            f.write("should be ignored")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("mmap.mmap")
    @patch("builtins.open")
    def test_initialization_and_scanning(self, mock_open, mock_mmap_cls):
        mock_map = MagicMock()
        mock_mmap_cls.return_value = mock_map
        
        browser = player_module.MP3Browser(self.test_dir)
        self.assertEqual(browser.cursor_idx, 0)
        self.assertEqual(browser.viewport_offset, 0)
        
        # Verify items scanned
        item_names = [item["name"] for item in browser.items]
        self.assertIn("Rock", item_names)
        self.assertIn("Pop", item_names)
        self.assertIn("song1.mp3", item_names)
        self.assertIn("song2.wma", item_names)
        self.assertNotIn("readme.txt", item_names)

    @patch("mmap.mmap")
    @patch("builtins.open")
    def test_directory_navigation(self, mock_open, mock_mmap_cls):
        mock_map = MagicMock()
        mock_mmap_cls.return_value = mock_map
        
        browser = player_module.MP3Browser(self.test_dir)
        
        # Move cursor to 'Rock' folder (it's alphabetically sorted: Pop, Rock, song1, song2)
        rock_idx = [i for i, x in enumerate(browser.items) if x["name"] == "Rock"][0]
        browser.cursor_idx = rock_idx
        
        browser.run_selected()
        
        # Verify we navigated inside 'Rock' folder
        self.assertTrue(browser.current_dir.endswith("Rock"))
        self.assertIn("..", [item["name"] for item in browser.items])

    @patch("subprocess.run")
    @patch("mmap.mmap")
    @patch("builtins.open")
    def test_playback_launch(self, mock_open, mock_mmap_cls, mock_run):
        mock_map = MagicMock()
        mock_mmap_cls.return_value = mock_map
        
        browser = player_module.MP3Browser(self.test_dir)
        
        # Select song1.mp3
        song_idx = [i for i, x in enumerate(browser.items) if x["name"] == "song1.mp3"][0]
        browser.cursor_idx = song_idx
        
        browser.run_selected()
        
        # Verify mpg123 was launched
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertIn("mpg123", args[0])


if __name__ == "__main__":
    unittest.main()