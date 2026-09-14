import unittest
import os
import json
import shutil
import tempfile
from unittest.mock import patch, MagicMock

# Import functions/classes from 2048
import datetime
from importlib import reload
import sys

# Ensure current dir is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import importlib
game_module = importlib.import_module("2048")


class TestGame2048(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.orig_score_file = game_module.SCORE_FILE
        self.orig_log_dir = game_module.LOG_DIR
        
        game_module.SCORE_FILE = os.path.join(self.test_dir, "test_high_scores.json")
        game_module.LOG_DIR = self.test_dir
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
        game_module.SCORE_FILE = self.orig_score_file
        game_module.LOG_DIR = self.orig_log_dir

    def test_initialization(self):
        # Test that Game2048 initializes properly
        game = game_module.Game2048()
        self.assertEqual(game.score, 0)
        self.assertEqual(game.recall_count, 0)
        self.assertEqual(game.step_count, 1)  # step_count starts at 0, logs initial, incrementing to 1
        self.assertEqual(len(game.history), 0)
        self.assertTrue(os.path.basename(game.log_file_path).startswith("2048_"))
        
        # Grid must have exactly two non-zero tiles
        flat_grid = [val for row in game.grid for val in row]
        non_zero_tiles = [val for val in flat_grid if val > 0]
        self.assertEqual(len(non_zero_tiles), 2)
        self.assertTrue(all(val in [2, 4] for val in non_zero_tiles))

    def test_logging(self):
        game = game_module.Game2048()
        # Ensure log file was created (mocking log path to our temp dir)
        temp_log = os.path.join(self.test_dir, "test_2048_game.log")
        game.log_file_path = temp_log
        
        # Log a dummy step
        game.log_step("w", (4, 1, 2))
        
        self.assertTrue(os.path.exists(temp_log))
        with open(temp_log, "r") as f:
            content = f.read()
            
        self.assertIn("--- STEP 1 ---", content)
        self.assertIn("Move: w", content)
        self.assertIn("Score: 0", content)
        self.assertIn("Added Tile: 4 at (1, 2)", content)

    def test_recall_step(self):
        game = game_module.Game2048()
        temp_log = os.path.join(self.test_dir, "test_2048_game.log")
        game.log_file_path = temp_log
        
        # Setup initial state
        game.grid = [
            [2, 0, 0, 0],
            [0, 2, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        game.score = 4
        
        # Simulate a move (slide left)
        # To simulate, we first push old state to history
        state_copy = {
            "grid": [row[:] for row in game.grid],
            "score": game.score,
            "has_won": game.has_won,
            "won_announced": game.won_announced,
        }
        game.history.append(state_copy)
        
        # Perform modification
        game.grid[0][0] = 4
        game.grid[0][1] = 0
        game.score = 8
        
        # Verify recall works
        self.assertEqual(len(game.history), 1)
        self.assertEqual(game.recall_count, 0)
        
        success = game.recall_step()
        
        self.assertTrue(success)
        self.assertEqual(game.recall_count, 1)
        self.assertEqual(game.score, 4)
        self.assertEqual(game.grid[0][0], 2)
        self.assertEqual(game.grid[0][1], 0)
        self.assertEqual(len(game.history), 0)

    def test_load_and_save_leaderboard(self):
        # Verify leaderboard functions handle file I/O and backward compatibility correctly
        # 1. No file scenario
        scores, best = game_module.load_leaderboard()
        self.assertEqual(scores, [])
        self.assertEqual(best, 0)
        
        # 2. Saving a leaderboard
        test_scores = [
            {"name": "Alice", "score": 2048, "recalls": 2, "date": "2026-09-14 12:00:00"},
            {"name": "Bob", "score": 1024, "recalls": 0, "date": "2026-09-14 12:01:00"}
        ]
        game_module.save_leaderboard(test_scores, 2048)
        
        # 3. Loading saved leaderboard
        loaded_scores, loaded_best = game_module.load_leaderboard()
        self.assertEqual(loaded_best, 2048)
        self.assertEqual(len(loaded_scores), 2)
        self.assertEqual(loaded_scores[0]["name"], "Alice")
        self.assertEqual(loaded_scores[1]["score"], 1024)

    def test_parse_log_file(self):
        # Create a mock log file content
        temp_log = os.path.join(self.test_dir, "test_parse.log")
        with open(temp_log, "w") as f:
            f.write("""--- STEP 0 ---
Move: Initial
Score: 0
Grid:
2 0 0 0
0 2 0 0
0 0 0 0
0 0 0 0
Added Tile: None

--- STEP 1 ---
Move: a
Score: 4
Grid:
4 0 0 0
2 0 0 0
0 0 0 0
0 0 2 0
Added Tile: 2 at (3, 2)
""")
            
        frames = game_module.parse_log_file(temp_log)
        self.assertEqual(len(frames), 2)
        self.assertEqual(frames[0]["step"], 0)
        self.assertEqual(frames[0]["move"], "Initial")
        self.assertEqual(frames[0]["score"], 0)
        self.assertEqual(frames[0]["grid"], [[2,0,0,0],[0,2,0,0],[0,0,0,0],[0,0,0,0]])
        self.assertEqual(frames[0]["added_tile"], "None")
        
        self.assertEqual(frames[1]["step"], 1)
        self.assertEqual(frames[1]["move"], "a")
        self.assertEqual(frames[1]["score"], 4)
        self.assertEqual(frames[1]["grid"], [[4,0,0,0],[2,0,0,0],[0,0,0,0],[0,0,2,0]])
        self.assertEqual(frames[1]["added_tile"], "2 at (3, 2)")

    @patch("rich.console.Console.print")
    @patch("rich.console.Console.clear")
    def test_render_playback(self, mock_clear, mock_print):
        grid = [[2, 0, 0, 0], [0, 4, 0, 0], [0, 0, 8, 0], [0, 0, 0, 16]]
        game_module.render_playback(
            grid=grid,
            score=32,
            step=5,
            total_steps=10,
            speed=1.5,
            move="w",
            added_tile="4 at (1, 1)",
            paused=True,
            inverted_mode=False
        )
        mock_clear.assert_called_once()
        mock_print.assert_called_once()

    @patch("time.sleep")
    @patch("rich.console.Console.print")
    @patch("rich.console.Console.clear")
    def test_play_fireworks_video(self, mock_clear, mock_print, mock_sleep):
        game_module.play_fireworks_video("TEST")
        self.assertTrue(mock_clear.call_count >= 10)
        self.assertTrue(mock_print.call_count >= 10)

    def test_can_move_in_direction(self):
        game = game_module.Game2048()
        # Set a controlled grid state
        game.grid = [
            [0, 0, 0, 2],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        self.assertTrue(game.can_move_in_direction("a"))   # Shift left from col 3 to col 0 is valid
        self.assertFalse(game.can_move_in_direction("d"))  # Shift right is invalid (already rightmost)

    def test_from_state(self):
        # Verify that Game2048.from_state correctly restores a state from playback
        grid = [[2, 4, 8, 16], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        score = 30
        history_frames = [
            {"grid": [[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]], "score": 4},
            {"grid": [[4, 4, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]], "score": 12}
        ]
        
        game = game_module.Game2048.from_state(grid, score, history_frames)
        
        self.assertEqual(game.grid, grid)
        self.assertEqual(game.score, score)
        self.assertEqual(len(game.history), 2)
        self.assertEqual(game.history[0]["score"], 4)
        self.assertEqual(game.history[1]["score"], 12)
        self.assertEqual(game.step_count, 3) # Starts at 2 historical frames, logs Grabbed Control (+1)
        self.assertTrue(os.path.basename(game.log_file_path).endswith("_interactive.log"))

    @patch("2048.get_key")
    @patch("rich.console.Console.print")
    @patch("rich.console.Console.clear")
    def test_show_help_screen(self, mock_clear, mock_print, mock_get_key):
        game_module.show_help_screen("game")
        mock_clear.assert_called_once()
        mock_print.assert_called_once()

    def test_simulate_move(self):
        grid = [
            [2, 2, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        next_grid, changed, gain = game_module.simulate_move(grid, "a")
        self.assertTrue(changed)
        self.assertEqual(gain, 4)
        self.assertEqual(next_grid[0], [4, 0, 0, 0])

    def test_evaluate_grid(self):
        corner_monotonic_grid = [
            [2, 4, 8, 16],
            [32, 64, 128, 256],
            [512, 1024, 2048, 4096],
            [8192, 16384, 32768, 65536]
        ]
        bad_grid = [
            [65536, 32768, 16384, 8192],
            [512, 1024, 2048, 4096],
            [32, 64, 128, 256],
            [2, 4, 8, 16]
        ]
        score_good = game_module.evaluate_grid(corner_monotonic_grid)
        score_bad = game_module.evaluate_grid(bad_grid)
        self.assertTrue(score_good > score_bad)

    def test_expectimax_choice(self):
        grid = [
            [2, 4, 2, 4],
            [4, 2, 4, 2],
            [2, 4, 2, 4],
            [4, 2, 4, 0]
        ]
        score = game_module.expectimax(grid, depth=2, is_player=True)
        self.assertTrue(isinstance(score, (int, float)))


if __name__ == "__main__":
    unittest.main()