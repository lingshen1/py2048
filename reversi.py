#!/usr/bin/env python3
"""
Reversi (Othello) - Standard 8x8 Game for Linux Framebuffer and Terminal
Author: Ling Shen
Version: v1.0.0
"""
import datetime
import json
import math
import mmap
import os
import random
import select
import shutil
import socket
import subprocess
import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

BITMAP_FONT = {
    '0': [0x3C, 0x66, 0x6E, 0x7E, 0x76, 0x66, 0x3C, 0x00],
    '1': [0x18, 0x38, 0x18, 0x18, 0x18, 0x18, 0x3C, 0x00],
    '2': [0x3C, 0x66, 0x06, 0x0C, 0x18, 0x30, 0x7E, 0x00],
    '3': [0x3C, 0x66, 0x06, 0x1C, 0x06, 0x66, 0x3C, 0x00],
    '4': [0x0C, 0x1C, 0x3C, 0x6C, 0x7E, 0x0C, 0x0C, 0x00],
    '5': [0x7E, 0x60, 0x7C, 0x06, 0x06, 0x66, 0x3C, 0x00],
    '6': [0x1C, 0x30, 0x60, 0x7C, 0x66, 0x66, 0x3C, 0x00],
    '7': [0x7E, 0x06, 0x0C, 0x18, 0x30, 0x30, 0x30, 0x00],
    '8': [0x3C, 0x66, 0x66, 0x3C, 0x66, 0x66, 0x3C, 0x00],
    '9': [0x3C, 0x66, 0x66, 0x3E, 0x06, 0x0C, 0x38, 0x00],
    's': [0x3E, 0x60, 0x7C, 0x06, 0x06, 0x66, 0x3C, 0x00],
    'c': [0x3C, 0x66, 0x60, 0x60, 0x60, 0x66, 0x3C, 0x00],
    'o': [0x3C, 0x66, 0x66, 0x66, 0x66, 0x66, 0x3C, 0x00],
    'r': [0x7C, 0x66, 0x66, 0x7C, 0x78, 0x6C, 0x66, 0x00],
    'e': [0x7E, 0x60, 0x7C, 0x60, 0x60, 0x60, 0x7E, 0x00],
    'b': [0x7C, 0x66, 0x66, 0x7C, 0x66, 0x66, 0x7C, 0x00],
    't': [0x7E, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x00],
    'g': [0x3E, 0x66, 0x60, 0x6E, 0x66, 0x66, 0x3E, 0x00],
    'a': [0x3C, 0x66, 0x66, 0x7E, 0x66, 0x66, 0x66, 0x00],
    'm': [0x66, 0x7E, 0x66, 0x66, 0x66, 0x66, 0x66, 0x00],
    'v': [0x66, 0x66, 0x66, 0x66, 0x66, 0x3C, 0x18, 0x00],
    'p': [0x7C, 0x66, 0x66, 0x7C, 0x60, 0x60, 0x60, 0x00],
    'l': [0x60, 0x60, 0x60, 0x60, 0x60, 0x60, 0x7E, 0x00],
    'y': [0x66, 0x66, 0x66, 0x3C, 0x18, 0x18, 0x18, 0x00],
    'n': [0x66, 0x6E, 0x7E, 0x76, 0x66, 0x66, 0x66, 0x00],
    'w': [0x66, 0x66, 0x66, 0x66, 0x7E, 0x7E, 0x66, 0x00],
    'i': [0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x00],
    'u': [0x66, 0x66, 0x66, 0x66, 0x66, 0x66, 0x3C, 0x00],
    'd': [0x78, 0x6C, 0x66, 0x66, 0x66, 0x6C, 0x78, 0x00],
    'h': [0x66, 0x66, 0x66, 0x7E, 0x66, 0x66, 0x66, 0x00],
    'k': [0x66, 0x6C, 0x78, 0x70, 0x78, 0x6C, 0x66, 0x00],
    ' ': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
    '-': [0x00, 0x00, 0x00, 0x7E, 0x00, 0x00, 0x00, 0x00],
    ':': [0x00, 0x18, 0x18, 0x00, 0x18, 0x18, 0x00, 0x00],
    '!': [0x18, 0x18, 0x18, 0x18, 0x18, 0x00, 0x18, 0x00],
    '?': [0x3C, 0x66, 0x06, 0x0C, 0x18, 0x00, 0x18, 0x00],
}


class FramebufferDisplay:
    def __init__(self):
        self.width = 320
        self.height = 320
        self.bpp = 4
        self.size_bytes = 320 * 320 * 4
        self.fb_file = None
        self.fb_map = None
        
        try:
            if os.path.exists("/sys/class/graphics/fb0/virtual_size"):
                with open("/sys/class/graphics/fb0/virtual_size", "r") as f:
                    w_str, h_str = f.read().strip().split(",")
                    self.width = int(w_str)
                    self.height = int(h_str)
            if os.path.exists("/sys/class/graphics/fb0/bits_per_pixel"):
                with open("/sys/class/graphics/fb0/bits_per_pixel", "r") as f:
                    bpp_bits = int(f.read().strip())
                    self.bpp = bpp_bits // 8
            if os.path.exists("/sys/class/graphics/fb0/size"):
                with open("/sys/class/graphics/fb0/size", "r") as f:
                    self.size_bytes = int(f.read().strip())
            else:
                self.size_bytes = self.width * self.height * self.bpp
        except Exception:
            pass
            
        try:
            self.fb_file = open("/dev/fb0", "r+b")
            self.fb_map = mmap.mmap(self.fb_file.fileno(), self.size_bytes)
            self.backbuffer = bytearray(self.size_bytes)
        except Exception as e:
            raise RuntimeError(f"Cannot initialize /dev/fb0: {e}")

    def get_pixel_color(self, r, g, b):
        if self.bpp == 4:
            return bytes([b, g, r, 0])
        else:
            r5 = (r >> 3) & 0x1F
            g6 = (g >> 2) & 0x3F
            b5 = (b >> 3) & 0x1F
            val = (r5 << 11) | (g6 << 5) | b5
            return bytes([val & 0xFF, (val >> 8) & 0xFF])

    def clear(self, r, g, b):
        color_bytes = self.get_pixel_color(r, g, b)
        self.backbuffer = bytearray(color_bytes * (self.width * self.height))

    def draw_rect(self, x, y, w, h, r, g, b):
        color_bytes = self.get_pixel_color(r, g, b)
        for dy in range(h):
            cy = y + dy
            if 0 <= cy < self.height:
                start_x = max(0, x)
                end_x = min(self.width, x + w)
                if start_x < end_x:
                    idx_start = (cy * self.width + start_x) * self.bpp
                    idx_end = (cy * self.width + end_x) * self.bpp
                    self.backbuffer[idx_start:idx_end] = color_bytes * (end_x - start_x)

    def draw_circle(self, cx, cy, radius, r, g, b):
        color_bytes = self.get_pixel_color(r, g, b)
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx*dx + dy*dy <= radius*radius:
                    px = cx + dx
                    py = cy + dy
                    if 0 <= px < self.width and 0 <= py < self.height:
                        idx = (py * self.width + px) * self.bpp
                        self.backbuffer[idx : idx + self.bpp] = color_bytes

    def draw_3d_circle(self, cx, cy, radius, is_white):
        # Specular light highlight offset towards the top-left
        lx = cx - radius // 3
        ly = cy - radius // 3
        
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx*dx + dy*dy <= radius*radius:
                    px = cx + dx
                    py = cy + dy
                    if 0 <= px < self.width and 0 <= py < self.height:
                        dist = math.sqrt((px - lx)**2 + (py - ly)**2)
                        
                        if dist < radius // 4:
                            # Shiny reflection specular highlight dot
                            r, g, b = (255, 255, 255) if is_white else (200, 200, 200)
                        else:
                            # Standard diffuse radial falloff shadow
                            factor = dist / (1.6 * radius)
                            factor = min(1.0, max(0.0, factor))
                            if is_white:
                                # Blend from pure shiny white to soft grey shadow
                                r = int(255 - factor * 135)
                                g = int(255 - factor * 135)
                                b = int(255 - factor * 135)
                            else:
                                # Blend from soft grey highlights to dark charcoal shadows
                                r = int(100 - factor * 95)
                                g = int(100 - factor * 95)
                                b = int(100 - factor * 95)
                                
                        idx = (py * self.width + px) * self.bpp
                        self.backbuffer[idx : idx + self.bpp] = self.get_pixel_color(r, g, b)

    def draw_char(self, char, x, y, scale, r, g, b):
        bitmap = BITMAP_FONT.get(char.lower(), BITMAP_FONT[' '])
        for row_idx, row_byte in enumerate(bitmap):
            for col_idx in range(8):
                if (row_byte >> (7 - col_idx)) & 1:
                    self.draw_rect(
                        x + col_idx * scale,
                        y + row_idx * scale,
                        scale,
                        scale,
                        r, g, b
                    )

    def draw_string(self, text, x, y, scale, r, g, b):
        cx = x
        for char in text:
            self.draw_char(char, cx, y, scale, r, g, b)
            cx += 8 * scale

    def flush(self):
        if self.fb_map:
            try:
                self.fb_map.seek(0)
                self.fb_map.write(self.backbuffer)
            except Exception:
                pass

    def close(self):
        if self.fb_map:
            try:
                self.fb_map.close()
            except Exception:
                pass
        if self.fb_file:
            try:
                self.fb_file.close()
            except Exception:
                pass


class RawTerminal:
    def __enter__(self):
        self.old_settings = os.popen("stty -g 2>/dev/null").read().strip()
        os.system("stty -icanon -echo 2>/dev/null")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.old_settings:
            os.system(f"stty {self.old_settings} 2>/dev/null")


def get_key():
    ch = sys.stdin.read(1)
    if ch == "\x1b":
        seq = sys.stdin.read(2)
        ch += seq
        if ch == "\x1b[A":
            return "w"
        elif ch == "\x1b[B":
            return "s"
        elif ch == "\x1b[C":
            return "d"
        elif ch == "\x1b[D":
            return "a"
    return ch.lower()


class ReversiGame:
    def __init__(self):
        # 8x8 Grid: 0=Empty, 1=Black(Human), 2=White(Bot)
        self.board = [[0] * 8 for _ in range(8)]
        self.board[3][3] = 2
        self.board[3][4] = 1
        self.board[4][3] = 1
        self.board[4][4] = 2
        
        self.current_turn = 1 # Black starts
        self.cursor_r = 3
        self.cursor_c = 2
        self.cursor_idx = 0
        
        # Positional value matrix for evaluation
        self.W_MATRIX = [
            [ 100, -15,  10,   5,   5,  10, -15, 100],
            [ -15, -30,  -3,  -3,  -3,  -3, -30, -15],
            [  10,  -3,   2,   2,   2,   2,  -3,  10],
            [   5,  -3,   2,   1,   1,   2,  -3,   5],
            [   5,  -3,   2,   1,   1,   2,  -3,   5],
            [  10,  -3,   2,   2,   2,   2,  -3,  10],
            [ -15, -30,  -3,  -3,  -3,  -3, -30, -15],
            [ 100, -15,  10,   5,   5,  10, -15, 100]
        ]
        
        self.fb_display = None
        if "-g" in sys.argv or "--graph" in sys.argv:
            try:
                self.fb_display = FramebufferDisplay()
            except Exception as e:
                console.print(f"[yellow]Failed to initialize graphical framebuffer: {e}[/yellow]")

    def __del__(self):
        if hasattr(self, "fb_display") and self.fb_display:
            self.fb_display.close()

    def count_discs(self):
        black = sum(row.count(1) for row in self.board)
        white = sum(row.count(2) for row in self.board)
        return black, white

    def get_valid_moves(self, color):
        valid_moves = {}
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == 0:
                    flips = self.is_valid_move(r, c, color)
                    if flips:
                        valid_moves[(r, c)] = flips
        return valid_moves

    def is_valid_move(self, r, c, color):
        opponent = 2 if color == 1 else 1
        flips = []
        
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        
        for dr, dc in directions:
            current_flips = []
            cr, cc = r + dr, c + dc
            
            while 0 <= cr < 8 and 0 <= cc < 8 and self.board[cr][cc] == opponent:
                current_flips.append((cr, cc))
                cr += dr
                cc += dc
                
            if 0 <= cr < 8 and 0 <= cc < 8 and self.board[cr][cc] == color:
                flips.extend(current_flips)
                
        return flips

    def execute_move(self, r, c, color):
        flips = self.is_valid_move(r, c, color)
        if not flips:
            return False
            
        self.board[r][c] = color
        for fr, fc in flips:
            self.board[fr][fc] = color
        return True

    # --- AI Bot Strategy (Minimax + Alpha-Beta Pruning) ---
    def evaluate_board(self, board_state):
        bot_color = 2
        player_color = 1
        
        black_count = sum(row.count(1) for row in board_state)
        white_count = sum(row.count(2) for row in board_state)
        total_discs = black_count + white_count
        
        # 1. Positional Matrix Weights Score
        positional_score = 0
        for r in range(8):
            for c in range(8):
                val = board_state[r][c]
                if val == bot_color:
                    positional_score += self.W_MATRIX[r][c]
                elif val == player_color:
                    positional_score -= self.W_MATRIX[r][c]
                    
        # 2. Dynamic Corner traps checking (If corner is empty, penalize adjacent cells)
        corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
        # List adjacent C and X squares for each corner
        adjacents = {
            (0, 0): [(0, 1), (1, 0), (1, 1)],
            (0, 7): [(0, 6), (1, 7), (1, 6)],
            (7, 0): [(6, 0), (7, 1), (6, 1)],
            (7, 7): [(7, 6), (6, 7), (6, 6)]
        }
        for (cr, cc), adj_list in adjacents.items():
            if board_state[cr][cc] == 0:
                for ar, ac in adj_list:
                    if board_state[ar][ac] == bot_color:
                        positional_score -= 50  # Penalize adjacent C/X-squares early
                    elif board_state[ar][ac] == player_color:
                        positional_score += 50
                        
        # 3. Mobility Score (Count potential legal moves)
        # We need a quick legal move count on simulated state
        def count_sim_moves(grid, color):
            count = 0
            for r in range(8):
                for c in range(8):
                    if grid[r][c] == 0:
                        # Quick check inline
                        has_flips = False
                        opponent = 1 if color == 2 else 2
                        directions = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
                        for dr, dc in directions:
                            cr, cc = r + dr, c + dc
                            path = []
                            while 0 <= cr < 8 and 0 <= cc < 8 and grid[cr][cc] == opponent:
                                path.append((cr,cc))
                                cr += dr
                                cc += dc
                            if 0 <= cr < 8 and 0 <= cc < 8 and grid[cr][cc] == color and path:
                                has_flips = True
                                break
                        if has_flips:
                            count += 1
            return count

        bot_mobility = count_sim_moves(board_state, bot_color)
        player_mobility = count_sim_moves(board_state, player_color)
        mobility_score = bot_mobility - player_mobility
        
        # 4. Disc Score difference
        disc_score = white_count - black_count
        
        # --- Multi-phase evaluation weight blending ---
        if total_discs < 52:
            # Early & Midgame: Prioritize corner/position, restrict mobility, MINIMIZE own discs (delayed max)
            score = positional_score + (15 * mobility_score) - (3 * disc_score)
        else:
            # Endgame: Maximize disc count and capture remaining territory!
            score = positional_score + (5 * mobility_score) + (100 * disc_score)
            
        return score

    def minimax(self, board_state, depth, alpha, beta, is_maximizing):
        # Quick termination check
        def has_any_moves(grid, color):
            for r in range(8):
                for c in range(8):
                    if grid[r][c] == 0:
                        opponent = 1 if color == 2 else 2
                        for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                            cr, cc = r + dr, c + dc
                            found = False
                            while 0 <= cr < 8 and 0 <= cc < 8 and grid[cr][cc] == opponent:
                                found = True
                                cr += dr
                                cc += dc
                            if 0 <= cr < 8 and 0 <= cc < 8 and grid[cr][cc] == color and found:
                                return True
            return False

        has_bot = has_any_moves(board_state, 2)
        has_player = has_any_moves(board_state, 1)
        
        if depth == 0 or (not has_bot and not has_player):
            return self.evaluate_board(board_state), None
            
        if is_maximizing:
            if not has_bot: # Pass turn
                return self.minimax(board_state, depth - 1, alpha, beta, False)[0], None
                
            best_val = -float('inf')
            best_move = None
            
            # Find all moves
            moves = []
            for r in range(8):
                for c in range(8):
                    if board_state[r][c] == 0:
                        # Find flips
                        flips = []
                        for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                            current_flips = []
                            cr, cc = r + dr, c + dc
                            while 0 <= cr < 8 and 0 <= cc < 8 and board_state[cr][cc] == 1:
                                current_flips.append((cr,cc))
                                cr += dr
                                cc += dc
                            if 0 <= cr < 8 and 0 <= cc < 8 and board_state[cr][cc] == 2:
                                flips.extend(current_flips)
                        if flips:
                            moves.append((r, c, flips))
                            
            # Sort moves by static value to optimize alpha-beta pruning cuts
            moves.sort(key=lambda x: self.W_MATRIX[x[0]][x[1]], reverse=True)
            
            for r, c, flips in moves:
                # Copy state
                sim_board = [row[:] for row in board_state]
                sim_board[r][c] = 2
                for fr, fc in flips:
                    sim_board[fr][fc] = 2
                    
                val, _ = self.minimax(sim_board, depth - 1, alpha, beta, False)
                if val > best_val:
                    best_val = val
                    best_move = (r, c)
                alpha = max(alpha, best_val)
                if beta <= alpha:
                    break
            return best_val, best_move
        else:
            if not has_player: # Pass turn
                return self.minimax(board_state, depth - 1, alpha, beta, True)[0], None
                
            best_val = float('inf')
            best_move = None
            
            moves = []
            for r in range(8):
                for c in range(8):
                    if board_state[r][c] == 0:
                        flips = []
                        for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                            current_flips = []
                            cr, cc = r + dr, c + dc
                            while 0 <= cr < 8 and 0 <= cc < 8 and board_state[cr][cc] == 2:
                                current_flips.append((cr,cc))
                                cr += dr
                                cc += dc
                            if 0 <= cr < 8 and 0 <= cc < 8 and board_state[cr][cc] == 1:
                                flips.extend(current_flips)
                        if flips:
                            moves.append((r, c, flips))
                            
            moves.sort(key=lambda x: self.W_MATRIX[x[0]][x[1]], reverse=True)
            
            for r, c, flips in moves:
                sim_board = [row[:] for row in board_state]
                sim_board[r][c] = 1
                for fr, fc in flips:
                    sim_board[fr][fc] = 1
                    
                val, _ = self.minimax(sim_board, depth - 1, alpha, beta, True)
                if val < best_val:
                    best_val = val
                    best_move = (r, c)
                beta = min(beta, best_val)
                if beta <= alpha:
                    break
            return best_val, best_move

    def get_best_bot_move(self):
        black, white = self.count_discs()
        total_discs = black + white
        # Adaptive search depth (4 in endgame for absolute endgame perfection!)
        depth = 4 if total_discs >= 50 else 3
        _, move = self.minimax(self.board, depth, -float('inf'), float('inf'), True)
        return move

    # --- Rendering Loops ---
    def render_text(self):
        console.clear()
        black, white = self.count_discs()
        
        table = Table(
            show_header=True,
            header_style="bold green",
            box=None,
            expand=False,
            title=f"🟢 REVERSI (OTHELLO) 🟢\n[bold cyan]Human (Black X): {black}[/bold cyan] | [bold magenta]Bot (White O): {white}[/bold magenta]"
        )
        
        table.add_column(" ", justify="center", width=3)
        for col in range(8):
            table.add_column(str(col + 1), justify="center", width=3)
            
        valid_moves = self.get_valid_moves(self.current_turn) if self.current_turn == 1 else {}
        
        for r in range(8):
            row_cells = [f"[bold yellow]{r+1}[/bold yellow]"]
            for c in range(8):
                val = self.board[r][c]
                is_cursor = (r == self.cursor_r and c == self.cursor_c)
                
                if val == 1:
                    cell_char = "X"
                    style = "bold cyan"
                elif val == 2:
                    cell_char = "O"
                    style = "bold white"
                elif (r, c) in valid_moves:
                    cell_char = "*"
                    style = "bold yellow blink"
                else:
                    cell_char = "."
                    style = "dim white"
                    
                if is_cursor:
                    row_cells.append(f"[bold reverse green] {cell_char} [/bold reverse green]")
                else:
                    row_cells.append(f"[{style}]{cell_char:^3}[/{style}]")
            table.add_row(*row_cells)
            
        panel = Panel(
            table,
            subtitle="[bold dim][Arrows/WASD] Move Cursor | [Space/Enter] Play Disc | [Q] Quit[/bold dim]",
            expand=False
        )
        console.print(panel)

    def render_graphical(self):
        if not self.fb_display:
            return
            
        width = self.fb_display.width
        height = self.fb_display.height
        
        # 1. Dark background
        self.fb_display.clear(30, 30, 30)
        
        # Get count
        black, white = self.count_discs()
        
        # 2. Render Score and Turns
        self.fb_display.draw_string("HUMAN:", 12, 10, 1, 0, 255, 255)
        self.fb_display.draw_string(str(black), 12, 22, 2, 255, 255, 255)
        
        self.fb_display.draw_string("BOT:", 205, 10, 1, 255, 105, 180)
        self.fb_display.draw_string(str(white), 205, 22, 2, 255, 255, 255)
        
        # Show whose turn it is
        if self.current_turn == 1:
            self.fb_display.draw_string("YOUR TURN", 100, 15, 1, 0, 255, 0)
        else:
            self.fb_display.draw_string("BOT THINKING...", 95, 15, 1, 255, 165, 0)
            
        # 3. Draw Wooden "Go-Board" Container (240x240 centered)
        grid_x = (width - 240) // 2
        grid_y = 65
        
        # Draw alternative wood squares (checkered warm-wood style)
        cell_step = 30
        for r in range(8):
            for c in range(8):
                cx = grid_x + c * cell_step
                cy = grid_y + r * cell_step
                # Checkered wood board color palette
                wood_color = (210, 180, 140) if (r + c) % 2 == 0 else (139, 90, 43)
                self.fb_display.draw_rect(cx, cy, cell_step, cell_step, *wood_color)
        
        # Draw grid lines (elegant thin dark-brown lines, matching real Go-board)
        for i in range(9):
            self.fb_display.draw_rect(grid_x, grid_y + i * 30, 240, 1, 90, 45, 10)
            self.fb_display.draw_rect(grid_x + i * 30, grid_y, 1, 240, 90, 45, 10)
        
        cell_size = 28
        offset = 1
        
        valid_moves = self.get_valid_moves(self.current_turn) if self.current_turn == 1 else {}
        
        for r in range(8):
            for c in range(8):
                val = self.board[r][c]
                cx = grid_x + offset + c * cell_step
                cy = grid_y + offset + r * cell_step
                
                # Draw 3D-Shaded Spherical Discs
                if val == 1:
                    # Shiny 3D Black disc (obsidian style)
                    self.fb_display.draw_3d_circle(cx + 14, cy + 14, 11, is_white=False)
                elif val == 2:
                    # Shiny 3D White disc (marble/ivory style)
                    self.fb_display.draw_3d_circle(cx + 14, cy + 14, 11, is_white=True)
                elif (r, c) in valid_moves:
                    # Yellow small dot for legal moves
                    self.fb_display.draw_circle(cx + 14, cy + 14, 3, 255, 215, 0)
                    
                # Draw Cursor selector (bright yellow hollow square outline)
                if r == self.cursor_r and c == self.cursor_c:
                    # Draw thick square borders
                    self.fb_display.draw_rect(cx, cy, cell_size, 2, 255, 215, 0) # top
                    self.fb_display.draw_rect(cx, cy + cell_size - 2, cell_size, 2, 255, 215, 0) # bottom
                    self.fb_display.draw_rect(cx, cy, 2, cell_size, 255, 215, 0) # left
                    self.fb_display.draw_rect(cx + cell_size - 2, cy, 2, cell_size, 255, 215, 0) # right
                    
        self.fb_display.flush()

    def render(self):
        if self.fb_display:
            self.render_graphical()
        else:
            self.render_text()


def is_sound_driver_detected():
    if os.path.exists("/proc/asound/cards"):
        try:
            with open("/proc/asound/cards", "r") as f:
                content = f.read().strip()
                if content and "no soundcards" not in content.lower():
                    return True
        except Exception:
            pass
    if os.path.exists("/dev/snd"):
        try:
            if os.listdir("/dev/snd"):
                return True
        except Exception:
            pass
    return False


def play_victory_song(test_mode=False):
    if not is_sound_driver_detected() or not shutil.which("aplay"):
        return

    sample_rate = 8000
    wave = bytearray()

    # Händel: See, the conquering hero comes!
    # Sol, Fa#, Sol, La, Sol, Fa#, Sol, Re, Si, La, Si, Do, Si, La, Si, Sol
    melody = [
        (784, 0.4), (740, 0.2), (784, 0.2), (880, 0.4), (784, 0.2), (740, 0.2), (784, 0.4), (587, 0.4),
        (0, 0.1),
        (988, 0.4), (880, 0.2), (988, 0.2), (1047, 0.4), (988, 0.2), (880, 0.2), (988, 0.4), (784, 0.4)
    ]

    for freq, duration in melody:
        num_samples = int(sample_rate * duration)
        if freq == 0:
            wave.extend([127] * num_samples)
        else:
            for i in range(num_samples):
                t = i / sample_rate
                val = int(127 + 120 * math.sin(2 * math.pi * freq * t))
                wave.append(val)

    # Setup subprocess args depending on test_mode
    # If test_mode is True, we don't suppress stderr/stdout and don't use -q (quiet) so they see ALSA outputs!
    aplay_args = ["aplay", "-t", "raw", "-r", "8000", "-f", "U8"]
    if not test_mode:
        aplay_args.insert(1, "-q")
        stdout_dest = subprocess.DEVNULL
        stderr_dest = subprocess.DEVNULL
    else:
        stdout_dest = None
        stderr_dest = None

    try:
        p = subprocess.Popen(
            aplay_args,
            stdin=subprocess.PIPE,
            stdout=stdout_dest,
            stderr=stderr_dest
        )
        if p and p.stdin:
            try:
                p.stdin.write(bytes(wave))
                p.stdin.flush()
            except Exception as e:
                if test_mode:
                    console.print(f"[red]Error writing wave bytes to aplay: {e}[/red]")
            finally:
                try:
                    p.stdin.close()
                except Exception:
                    pass
    except Exception as e:
        if test_mode:
            console.print(f"[red]Error spawning aplay subprocess: {e}[/red]")


def play_graphical_celebration(display, text="YOU WIN!"):
    width = display.width
    height = display.height
    
    colors = [
        (255, 0, 0), (0, 255, 0), (255, 215, 0), (0, 255, 255), (255, 0, 255),
        (255, 255, 255), (255, 127, 0), (127, 255, 0), (0, 127, 255)
    ]
    
    fireworks = [
        {"cx": width // 3, "cy": height - 10, "tx": width // 3, "ty": height // 3, "color": (255, 0, 0), "particles": [], "state": "launch"},
        {"cx": (2 * width) // 3, "cy": height - 10, "tx": (2 * width) // 3, "ty": height // 4, "color": (0, 255, 0), "particles": [], "state": "launch"}
    ]
    
    play_victory_song()
    
    for frame in range(40):
        display.clear(20, 20, 20)
        
        for fw in fireworks:
            if fw["state"] == "launch":
                if fw["cy"] > fw["ty"]:
                    fw["cy"] -= 6
                    display.draw_rect(fw["cx"] - 1, fw["cy"] - 1, 3, 6, *fw["color"])
                else:
                    fw["state"] = "explode"
                    num_particles = 12
                    for i in range(num_particles):
                        angle = (i * 2 * math.pi) / num_particles
                        speed = random.uniform(2.0, 4.5)
                        fw["particles"].append({
                            "x": float(fw["cx"]),
                            "y": float(fw["cy"]),
                            "vx": math.cos(angle) * speed,
                            "vy": math.sin(angle) * speed,
                        })
            elif fw["state"] == "explode":
                alive = False
                for p in fw["particles"]:
                    p["x"] += p["vx"]
                    p["y"] += p["vy"]
                    p["vy"] += 0.25
                    
                    px = int(round(p["x"]))
                    py = int(round(p["y"]))
                    
                    if 0 <= px < width and 0 <= py < height:
                        display.draw_rect(px - 1, py - 1, 3, 3, *fw["color"])
                        alive = True
                        
                if not alive and frame < 25:
                    fw["state"] = "launch"
                    fw["cx"] = random.randint(30, width - 30)
                    fw["cy"] = height - 10
                    fw["tx"] = fw["cx"]
                    fw["ty"] = random.randint(30, height // 2)
                    fw["color"] = random.choice(colors)
                    fw["particles"] = []
                    
        text_len = len(text)
        text_w = text_len * 16
        text_x = (width - text_w) // 2
        text_y = height // 2 - 10
        
        tx_color = colors[frame % len(colors)]
        display.draw_rect(text_x - 10, text_y - 8, text_w + 20, 28, 10, 10, 10)
        display.draw_string(text, text_x, text_y, 2, *tx_color)
        
        display.flush()
        time.sleep(0.08)


def play_text_celebration(text="YOU WIN!"):
    width = 50
    height = 18
    colors = ["red", "green", "yellow", "blue", "magenta", "cyan", "white", "bright_yellow", "bright_cyan"]
    
    fireworks = [
        {"cx": 15, "cy": 16, "tx": 15, "ty": 5, "color": "bright_red", "particles": [], "state": "launch", "char": "^"},
        {"cx": 35, "cy": 16, "tx": 35, "ty": 6, "color": "bright_green", "particles": [], "state": "launch", "char": "^"},
    ]
    
    play_victory_song()
    
    for frame in range(40):
        grid = [[" "] * width for _ in range(height)]
        
        for fw in fireworks:
            if fw["state"] == "launch":
                if fw["cy"] > fw["ty"]:
                    fw["cy"] -= 1
                    grid[fw["cy"]][fw["cx"]] = f"[bold {fw['color']}]{fw['char']}[/bold {fw['color']}]"
                else:
                    fw["state"] = "explode"
                    num_particles = 12
                    for i in range(num_particles):
                        angle = (i * 2 * math.pi) / num_particles
                        speed = random.uniform(1.2, 2.8)
                        fw["particles"].append({
                            "x": float(fw["cx"]),
                            "y": float(fw["cy"]),
                            "vx": math.cos(angle) * speed * 1.6,
                            "vy": math.sin(angle) * speed * 0.8,
                            "char": random.choice(["*", "o", "+", "."])
                        })
            elif fw["state"] == "explode":
                alive = False
                for p in fw["particles"]:
                    p["x"] += p["vx"]
                    p["y"] += p["vy"]
                    p["vy"] += 0.08
                    
                    px = int(round(p["x"]))
                    py = int(round(p["y"]))
                    
                    if 0 <= px < width and 0 <= py < height:
                        grid[py][px] = f"[bold {fw['color']}]{p['char']}[/bold {fw['color']}]"
                        alive = True
                
                if not alive and frame < 25:
                    fw["state"] = "launch"
                    fw["cx"] = random.randint(8, width - 8)
                    fw["cy"] = height - 1
                    fw["tx"] = fw["cx"]
                    fw["ty"] = random.randint(3, height - 7)
                    fw["color"] = random.choice(colors)
                    fw["particles"] = []
                    
        text_len = len(text)
        text_x = (width - text_len) // 2
        text_y = height // 2
        
        text_color = colors[frame % len(colors)]
        text_styled = f"[bold {text_color}]{text}[/bold {text_color}]"
        
        console.clear()
        out = []
        for y in range(height):
            if y == text_y:
                left = "".join(grid[y][:text_x])
                right = "".join(grid[y][text_x + text_len:])
                out.append(left + text_styled + right)
            else:
                out.append("".join(grid[y]))
                
        panel = Panel("\n".join(out), title="🎉 CONGRATULATIONS! 🎉", expand=False)
        console.print(panel)
        time.sleep(0.08)


REVERSI_SCORE_FILE = "reversi_high_scores.json"


def load_reversi_leaderboard():
    if os.path.exists(REVERSI_SCORE_FILE):
        try:
            with open(REVERSI_SCORE_FILE, "r") as f:
                data = json.load(f)
                return data.get("scores", []), data.get("high_score", 0)
        except Exception:
            return [], 0
    return [], 0


def save_reversi_leaderboard(scores, high_score):
    try:
        with open(REVERSI_SCORE_FILE, "w") as f:
            json.dump({"high_score": high_score, "scores": scores}, f, indent=4)
    except Exception as e:
        console.print(f"[red]Error saving Reversi high scores: {e}[/red]")


def display_reversi_leaderboard():
    scores, historical_best = load_reversi_leaderboard()
    table = Table(title="🏆 REVERSI LEADERBOARD (TOP 20) 🏆", expand=False)
    table.add_column("Rank", justify="center", style="yellow")
    table.add_column("Player", justify="left", style="cyan")
    table.add_column("Your Discs", justify="right", style="green")
    table.add_column("Bot Discs", justify="right", style="magenta")
    table.add_column("Date", justify="center", style="dim white")
    
    sorted_scores = sorted(scores, key=lambda x: x.get("score", 0), reverse=True)[:20]
    
    for idx, item in enumerate(sorted_scores):
        table.add_row(
            str(idx + 1),
            item.get("name", "Anonymous"),
            str(item.get("score", 0)),
            str(item.get("bot_score", 0)),
            item.get("date", "N/A")
        )
        
    if not sorted_scores:
        table.add_row("-", "No high scores yet!", "0", "0", "-")
        
    console.print(table)


def check_and_save_reversi_leaderboard(score, bot_score, game=None):
    scores, historical_best = load_reversi_leaderboard()
    
    # Always celebrate if the player wins!
    if score > bot_score:
        text_video = "YOU DEFEATED THE BOT!"
        if game is not None and hasattr(game, "fb_display") and game.fb_display:
            play_graphical_celebration(game.fb_display, text_video)
        else:
            play_text_celebration(text_video)
        console.print(f"\n[bold green]🏆 CONGRATULATIONS! You defeated the AI Bot {score} to {bot_score}! 🏆[/bold green]")
        
    is_qualifying = False
    if len(scores) < 20:
        is_qualifying = True
    else:
        min_score = min(item.get("score", 0) for item in scores)
        if score > min_score:
            is_qualifying = True
            
    if is_qualifying:
        all_time_best = max([item.get("score", 0) for item in scores] + [historical_best])
        is_all_time_best = (score > all_time_best) or (not scores and score > 0)
        
        console.print("\n[bold yellow]🏆 YOU ACHIEVED A REVERSI LEADERBOARD HIGH SCORE! 🏆[/bold yellow]")
        try:
            player_name = input("Enter your name (max 15 chars): ").strip()
        except (KeyboardInterrupt, EOFError):
            player_name = "Anonymous"
            
        if not player_name:
            player_name = "Anonymous"
        player_name = player_name[:15]
        
        new_entry = {
            "name": player_name,
            "score": score,
            "bot_score": bot_score,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        scores.append(new_entry)
        scores = sorted(scores, key=lambda x: x.get("score", 0), reverse=True)[:20]
        
        new_historical_best = max(score, historical_best)
        save_reversi_leaderboard(scores, new_historical_best)
        console.print("\n[bold green]Reversi high score saved successfully![/bold green]\n")
    else:
        if score > bot_score:
            console.print(f"\n[bold yellow]Your score: {score} did not make the top 20 leaderboard.[/bold yellow]\n")
        else:
            console.print(f"\n[bold yellow]Your score: {score} (Bot: {bot_score}) did not make the top 20 leaderboard.[/bold yellow]\n")
        
    display_reversi_leaderboard()


def main():
    if "-p" in sys.argv or "--play-song" in sys.argv:
        if not is_sound_driver_detected():
            console.print("[red]Error: No active ALSA soundcard or driver detected.[/red]")
            return
        if not shutil.which("aplay"):
            console.print("[red]Error: ALSA 'aplay' utility not found in system PATH.[/red]")
            return
            
        console.print("[green]Playing Händel's 'See, the conquering hero comes!' victory melody as a test...[/green]")
        play_victory_song(test_mode=True)
        # Keep process alive for 5.5s so background aplay can complete playing the piped audio
        time.sleep(5.5)
        return

    game = ReversiGame()
    
    with RawTerminal():
        while True:
            game.render()
            
            # 1. Determine valid moves
            valid_moves = game.get_valid_moves(game.current_turn)
            
            # If no valid moves, they must pass
            if not valid_moves:
                opponent = 2 if game.current_turn == 1 else 1
                opponent_moves = game.get_valid_moves(opponent)
                
                if not opponent_moves:
                    # Both players have no moves, GAME OVER!
                    break
                else:
                    # Pass turn
                    game.current_turn = opponent
                    # Reset cursor to first valid move of opponent
                    op_list = list(opponent_moves.keys())
                    game.cursor_r, game.cursor_c = op_list[0]
                    continue
            
            # 2. Process Turn
            if game.current_turn == 1:
                # Human Turn (Black) - Snap cursor to valid moves
                valid_coords = sorted(list(valid_moves.keys()))
                if (game.cursor_r, game.cursor_c) not in valid_coords:
                    game.cursor_r, game.cursor_c = valid_coords[0]
                    game.cursor_idx = 0
                else:
                    game.cursor_idx = valid_coords.index((game.cursor_r, game.cursor_c))

                try:
                    key = get_key()
                except (KeyboardInterrupt, EOFError):
                    break
                    
                if key == "q":
                    console.print("\n[yellow]Game exited.[/yellow]\n")
                    black, white = game.count_discs()
                    if black > white:
                        check_and_save_reversi_leaderboard(black, white, game)
                    return
                elif key in ["d", "s"]: # Forward step in valid moves
                    game.cursor_idx = (game.cursor_idx + 1) % len(valid_coords)
                    game.cursor_r, game.cursor_c = valid_coords[game.cursor_idx]
                elif key in ["a", "w"]: # Backward step in valid moves
                    game.cursor_idx = (game.cursor_idx - 1) % len(valid_coords)
                    game.cursor_r, game.cursor_c = valid_coords[game.cursor_idx]
                elif key in [" ", "\r", "\n"]:
                    game.execute_move(game.cursor_r, game.cursor_c, 1)
                    # Switch to bot
                    game.current_turn = 2
            else:
                # Bot Turn (White)
                game.render()
                time.sleep(0.6)
                
                bot_move = game.get_best_bot_move()
                if bot_move is not None:
                    br, bc = bot_move
                    game.execute_move(br, bc, 2)
                # Switch to human
                game.current_turn = 1
                
                # Reset human cursor to first valid move (if any)
                human_moves = game.get_valid_moves(1)
                if human_moves:
                    hm_list = sorted(list(human_moves.keys()))
                    game.cursor_r, game.cursor_c = hm_list[0]
                    game.cursor_idx = 0
                    
    # --- Game Over Celebrations ---
    black, white = game.count_discs()
    console.clear()
    
    if black > white:
        check_and_save_reversi_leaderboard(black, white, game)
    elif white > black:
        console.print(f"\n[bold red]💀 GAME OVER! The AI Bot defeated you {white} to {black}.[/bold red]\n")
        display_reversi_leaderboard()
    else:
        console.print(f"\n[bold yellow]🤝 TIE GAME! You tied with the AI Bot {black} to {white}.[/bold yellow]\n")
        display_reversi_leaderboard()


if __name__ == "__main__":
    main()