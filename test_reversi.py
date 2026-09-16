import unittest
import os
import json
import shutil
import tempfile
from unittest.mock import patch, MagicMock

# Import Reversi Game
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import reversi as game_module


class TestReversiGame(unittest.TestCase):

    def test_initialization(self):
        game = game_module.ReversiGame()
        self.assertEqual(game.current_turn, 1) # Black starts
        self.assertEqual(game.board[3][3], 2) # White
        self.assertEqual(game.board[3][4], 1) # Black
        self.assertEqual(game.board[4][3], 1) # Black
        self.assertEqual(game.board[4][4], 2) # White
        
        # Test initial score counts
        b, w = game.count_discs()
        self.assertEqual(b, 2)
        self.assertEqual(w, 2)

    def test_get_valid_moves(self):
        game = game_module.ReversiGame()
        # For Black (1) on start, valid moves are (2,3), (3,2), (4,5), (5,4)
        moves = game.get_valid_moves(1)
        self.assertEqual(len(moves), 4)
        self.assertIn((2, 3), moves)
        self.assertIn((3, 2), moves)
        self.assertIn((4, 5), moves)
        self.assertIn((5, 4), moves)
        
        # Placing at (2,2) is invalid on start
        self.assertFalse(game.is_valid_move(2, 2, 1))

    def test_execute_move(self):
        game = game_module.ReversiGame()
        # Black plays (3, 2)
        success = game.execute_move(3, 2, 1)
        self.assertTrue(success)
        
        # Verify the tile was placed and (3, 3) was flipped from White (2) to Black (1)
        self.assertEqual(game.board[3][2], 1)
        self.assertEqual(game.board[3][3], 1)
        
        # Counts must now be Black: 4, White: 1
        b, w = game.count_discs()
        self.assertEqual(b, 4)
        self.assertEqual(w, 1)

    def test_ai_board_evaluation(self):
        game = game_module.ReversiGame()
        # Evaluation should work without any error
        score = game.evaluate_board(game.board)
        self.assertTrue(isinstance(score, (int, float)))

    def test_minimax_bot(self):
        game = game_module.ReversiGame()
        # Minimax should find a move for White (2) on initial board state (simulating)
        best_val, best_move = game.minimax(game.board, depth=2, alpha=-float('inf'), beta=float('inf'), is_maximizing=True)
        self.assertTrue(isinstance(best_val, (int, float)))
        self.assertIsNotNone(best_move)
        
        # Verified coordinate is inside 8x8 board
        r, c = best_move
        self.assertTrue(0 <= r < 8)
        self.assertTrue(0 <= c < 8)

    @patch("reversi.get_key")
    @patch("rich.console.Console.print")
    @patch("rich.console.Console.clear")
    def test_render_text(self, mock_clear, mock_print, mock_get_key):
        # Verify text renderer executes cleanly
        game = game_module.ReversiGame()
        game.render_text()
        mock_clear.assert_called_once()
        mock_print.assert_called_once()

    @patch("mmap.mmap")
    @patch("builtins.open")
    def test_graphical_display_reversi(self, mock_open, mock_mmap_cls):
        mock_map = MagicMock()
        mock_mmap_cls.return_value = mock_map
        
        display = game_module.FramebufferDisplay()
        display.clear(0, 0, 0)
        display.draw_circle(100, 100, 10, 255, 255, 255)
        display.draw_string("WIN", 10, 10, 1, 255, 0, 0)
        display.flush()
        
        mock_map.seek.assert_called_with(0)
        mock_map.write.assert_called_with(display.backbuffer)


if __name__ == "__main__":
    unittest.main()