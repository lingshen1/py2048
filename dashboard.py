#!/usr/bin/env python3
"""
Calculinux Graphical Dashboard Launcher (4x4 Grid)
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
    'f': [0x7E, 0x60, 0x7C, 0x60, 0x60, 0x60, 0x60, 0x00],
    'x': [0x66, 0x66, 0x24, 0x18, 0x24, 0x66, 0x66, 0x00],
    'j': [0x0E, 0x06, 0x06, 0x06, 0x06, 0x66, 0x3C, 0x00],
    'q': [0x3C, 0x66, 0x66, 0x3E, 0x06, 0x0E, 0x3D, 0x00],
    'z': [0x7E, 0x06, 0x0C, 0x18, 0x30, 0x60, 0x7E, 0x00],
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
            self.icon_cache = {}
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

    def draw_rounded_rect_3d(self, x, y, w, h, R, r, g, b, is_selected=False):
        # High performance 3D rounded button with lighting specular effect
        # Cached to avoid repeating calculations
        cache_key = (w, h, R, r, g, b, is_selected)
        if cache_key not in self.icon_cache:
            buf = bytearray(w * h * self.bpp)
            diag = float(w + h)
            
            for py in range(h):
                for px in range(w):
                    dx = px
                    dy = py
                    
                    # Rounded Corner clipping
                    if dx < R and dy < R:
                        if (R - 1 - dx)**2 + (R - 1 - dy)**2 > R*R:
                            continue
                    elif dx >= w - R and dy < R:
                        if (dx - (w - R))**2 + (R - 1 - dy)**2 > R*R:
                            continue
                    elif dx < R and dy >= h - R:
                        if (R - 1 - dx)**2 + (dy - (h - R))**2 > R*R:
                            continue
                    elif dx >= w - R and dy >= h - R:
                        if (dx - (w - R))**2 + (dy - (h - R))**2 > R*R:
                            continue
                    
                    # Draw a nice gold/cyan selection border outline if selected
                    if is_selected and (dx < 3 or dx >= w - 3 or dy < 3 or dy >= h - 3):
                        pixel_bytes = self.get_pixel_color(0, 255, 255) # Cyan highlight
                    else:
                        # 3D shading specular gradient (light from top-left)
                        factor = (dx + dy) / diag
                        if factor < 0.15:
                            h_weight = (1.0 - factor / 0.15) * 0.35
                            pr = int(r + (255 - r) * h_weight)
                            pg = int(g + (255 - g) * h_weight)
                            pb = int(b + (255 - b) * h_weight)
                        elif factor > 0.85:
                            s_weight = 0.65 + 0.35 * (1.0 - (factor - 0.85) / 0.15)
                            pr = int(r * s_weight)
                            pg = int(g * s_weight)
                            pb = int(b * s_weight)
                        else:
                            slope = 1.1 - 0.45 * ((factor - 0.15) / 0.70)
                            pr = int(min(255, r * slope))
                            pg = int(min(255, g * slope))
                            pb = int(min(255, b * slope))
                        pixel_bytes = self.get_pixel_color(pr, pg, pb)
                        
                    idx = (py * w + px) * self.bpp
                    buf[idx : idx + self.bpp] = pixel_bytes
            self.icon_cache[cache_key] = buf
            
        # Fast blit block memory copy
        cache_data = self.icon_cache[cache_key]
        row_bytes = w * self.bpp
        for dy in range(h):
            cy = y + dy
            if 0 <= cy < self.height:
                idx_back = (cy * self.width + x) * self.bpp
                idx_cache = dy * row_bytes
                self.backbuffer[idx_back : idx_back + row_bytes] = cache_data[idx_cache : idx_cache + row_bytes]

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


class CalculinuxDashboard:
    def __init__(self):
        self.display = FramebufferDisplay()
        self.cursor_r = 0
        self.cursor_c = 0
        
        # 4x4 Grid of Applications (Total 16 Slots)
        # Name: string labels shown below icons
        # Cmd: local execution command via subprocess
        # Icon: large character drawn inside the rounded box
        # Color: standard RGB colors for the 3D button background
        self.grid = [
            [
                {"name": "Calc", "cmd": "python3 /home/root/apps/calc.py", "icon": "C", "color": (220, 20, 60)},
                {"name": "Tmux", "cmd": "tmux new-session -A -s calculinux", "icon": "T", "color": (34, 139, 34)},
                {"name": "Reversi", "cmd": "python3 /home/root/apps/py2048/reversi.py -g", "icon": "R", "color": (139, 90, 43)},
                {"name": "2048", "cmd": "python3 /home/root/apps/py2048/2048.py -g", "icon": "2", "color": (255, 215, 0)}
            ],
            [
                {"name": "NES", "cmd": "/home/root/games/RomCollection/nes/s /home/root/games/RomCollection/nes/s/super_mario_brothers_duck_hunt.nes", "icon": "N", "color": (30, 144, 255)},
                {"name": "Python", "cmd": "python3", "icon": "P", "color": (148, 0, 211)},
                {"name": "WiFi", "cmd": "/home/root/wifi_connect.sh", "icon": "W", "color": (0, 206, 209)},
                {"name": "Bluetooth", "cmd": "/home/root/connect_bt.sh", "icon": "B", "color": (255, 69, 0)}
            ],
            [
                {"name": "mc", "cmd": "HOME=/home/root mc", "icon": "M", "color": (46, 139, 87)},
                {"name": "Top", "cmd": "top", "icon": "O", "color": (112, 128, 144)},
                {"name": "Dogfight", "cmd": "python3 /home/root/apps/dogfight.py", "icon": "D", "color": (218, 165, 32)},
                {"name": "CalcBig", "cmd": "python3 /home/root/apps/bigcalc.py", "icon": "K", "color": (255, 105, 180)}
            ],
            [
                {"name": "Music", "cmd": "python3 /home/root/apps/py2048/music_player.py -g", "icon": "U", "color": (70, 130, 180)},
                {"name": "Shell", "cmd": "/bin/sh -i", "icon": "S", "color": (128, 128, 128)},
                {"name": "RevText", "cmd": "python3 /home/root/apps/py2048/reversi.py", "icon": "V", "color": (0, 128, 128)},
                {"name": "2048Text", "cmd": "python3 /home/root/apps/py2048/2048.py", "icon": "8", "color": (128, 0, 0)}
            ]
        ]

    def render(self):
        # 1. Clear Screen
        self.display.clear(25, 25, 25)
        
        # 2. Draw Top Status Header (Moved up, height 24px)
        self.display.draw_rect(0, 0, 320, 24, 15, 15, 15)
        self.display.draw_string("CALCULINUX DASHBOARD", 10, 6, 1, 255, 215, 0)
        
        # Draw battery and wifi status indicator placeholders in top-right
        self.display.draw_string("WIFI", 240, 6, 1, 0, 255, 255)
        self.display.draw_string("100%", 280, 6, 1, 0, 255, 0)
        
        # 3. Draw 4x4 Grid (Each cell is 80x64 pixels total slot, moved up!)
        icon_w = 54
        icon_h = 42
        offset_y = 26
        
        for r in range(4):
            for c in range(4):
                app = self.grid[r][c]
                is_selected = (r == self.cursor_r and c == self.cursor_c)
                
                # Center coordinates within the 80x64 slot
                slot_x = c * 80
                slot_y = offset_y + r * 64
                
                cell_x = slot_x + 13
                cell_y = slot_y + 4
                
                # Draw 3D rounded colored block background
                self.display.draw_rounded_rect_3d(
                    cell_x, cell_y, icon_w, icon_h, 8,
                    *app["color"], is_selected=is_selected
                )
                
                # Draw the App Icon Letter (Centered scale 3, very big and nice!)
                # 8px letter width * scale 3 = 24px wide. Centered: (54 - 24) // 2 = 15 offset
                self.display.draw_char(
                    app["icon"], cell_x + 15, cell_y + 9, 3, 255, 255, 255
                )
                
                # Draw the App Name Label below the rounded box (centered, scale 1)
                label = app["name"]
                # 8px letter width * scale 1 = 8px wide. Centered: (80 - len*8) // 2
                label_x = slot_x + (80 - len(label) * 8) // 2
                label_y = slot_y + 50
                
                label_color = (255, 215, 0) if is_selected else (200, 200, 200)
                self.display.draw_string(label, label_x, label_y, 1, *label_color)
                
        self.display.flush()

    def run_app(self, name, cmd):
        # 1. Clear and release FB display resources
        self.display.clear(0, 0, 0)
        self.display.flush()
        
        # 2. Check if we are running inside a TMUX session for non-blocking multi-window multitasking!
        if "TMUX" in os.environ:
            # Query active window names to see if this application is already running in background
            try:
                res = subprocess.run(
                    ["tmux", "list-windows", "-F", "#{window_name}"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2.0
                )
                active_windows = [line.strip() for line in res.stdout.splitlines() if line.strip()]
            except Exception:
                active_windows = []

            if name in active_windows:
                # App is already running in the background! Seamlessly switch back/select its existing window!
                tmux_cmd = f"tmux select-window -t '{name}'"
            else:
                # App is not running yet! Spawn it in a new window!
                tmux_cmd = f"tmux new-window -n '{name}' '{cmd}'"
                
            try:
                subprocess.run(tmux_cmd, shell=True)
            except Exception as e:
                console.print(f"[red]Error navigating tmux: {e}[/red]")
                time.sleep(1.0)
        else:
            # Standalone blocking mode: Spawn and run locally in canonical terminal mode (stty restored)
            console.clear()
            console.print(f"[bold green]Launching: {cmd}...[/bold green]\n")
            try:
                subprocess.run(cmd, shell=True)
            except Exception as e:
                console.print(f"[red]Error running application: {e}[/red]")
                time.sleep(2.0)
                
            console.clear()


def main():
    dashboard = CalculinuxDashboard()
    
    with RawTerminal():
        while True:
            dashboard.render()
            
            try:
                key = get_key()
            except (KeyboardInterrupt, EOFError):
                break
                
            if key == "q":
                dashboard.display.clear(0, 0, 0)
                dashboard.display.flush()
                console.clear()
                console.print("[yellow]Calculinux Dashboard exited.[/yellow]")
                break
            elif key == "a": # Left
                dashboard.cursor_c = (dashboard.cursor_c - 1) % 4
            elif key == "d": # Right
                dashboard.cursor_c = (dashboard.cursor_c + 1) % 4
            elif key == "w": # Up
                dashboard.cursor_r = (dashboard.cursor_r - 1) % 4
            elif key == "s": # Down
                dashboard.cursor_r = (dashboard.cursor_r + 1) % 4
            elif key in [" ", "\r", "\n"]:
                # Launch application!
                app = dashboard.grid[dashboard.cursor_r][dashboard.cursor_c]
                
                if "TMUX" in os.environ:
                    # In TMUX: launch non-blockingly directly in a new window!
                    dashboard.run_app(app["name"], app["cmd"])
                else:
                    # Standalone mode: Temporarily suspend RawTerminal wrapper settings to let launched app run locally
                    os.system("stty sane 2>/dev/null")
                    dashboard.run_app(app["name"], app["cmd"])
                    os.system("stty -icanon -echo 2>/dev/null")


if __name__ == "__main__":
    main()