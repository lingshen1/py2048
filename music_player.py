#!/usr/bin/env python3
"""
Calculinux Graphical & Terminal MP3 Music Player Browser
Author: Ling Shen
Version: v1.0.0
"""
import os
import sys
import time
import mmap
import math
import shutil
import select
import subprocess
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
    '/': [0x00, 0x06, 0x0C, 0x18, 0x30, 0x60, 0x40, 0x00],
    '.': [0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x18, 0x00],
    '<': [0x0C, 0x18, 0x30, 0x60, 0x30, 0x18, 0x0C, 0x00],
    '>': [0x30, 0x18, 0x0C, 0x06, 0x0C, 0x18, 0x30, 0x00],
    '[': [0x3C, 0x30, 0x30, 0x30, 0x30, 0x30, 0x3C, 0x00],
    ']': [0x3C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x3C, 0x00],
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


class MP3Browser:
    def __init__(self, root_dir="/home/root/music"):
        self.root_dir = os.path.abspath(root_dir)
        self.current_dir = self.root_dir
        
        # Ensure music folder exists
        if not os.path.exists(self.current_dir):
            try:
                os.makedirs(self.current_dir, exist_ok=True)
            except Exception:
                pass
                
        self.cursor_idx = 0
        self.viewport_offset = 0
        self.items = []
        self.tagged_files = set() # Store full paths of tagged/selected files
        
        # Check if running in graphical mode
        self.graphical_mode = "-g" in sys.argv
        self.fb_display = None
        if self.graphical_mode:
            try:
                self.fb_display = FramebufferDisplay()
            except Exception as e:
                console.print(f"[red]Cannot start graphical mode: {e}. Falling back to terminal.[/red]")
                self.graphical_mode = False
                time.sleep(2.0)
                
        self.scan_directory()

    def scan_dir_files(self, path):
        # Scan and return sorted list of folders and files
        try:
            raw_entries = os.listdir(path)
        except Exception:
            return []
            
        dirs = []
        files = []
        
        # Add parent folder option if not at the root directory
        if os.path.abspath(path) != os.path.abspath(self.root_dir):
            dirs.append({"name": "..", "is_dir": True})
            
        for name in sorted(raw_entries):
            full_path = os.path.join(path, name)
            is_dir = os.path.isdir(full_path)
            
            # We filter for folders or MP3/WMA files
            if is_dir:
                dirs.append({"name": name, "is_dir": True})
            elif name.lower().endswith((".mp3", ".wma")):
                files.append({"name": name, "is_dir": False})
                
        return dirs + files

    def scan_directory(self):
        self.items = self.scan_dir_files(self.current_dir)
        self.cursor_idx = 0
        self.viewport_offset = 0

    def draw_terminal(self):
        console.clear()
        
        table = Table(
            title=f"🎵 CALCULINUX MP3 PLAYER BROWSER 🎵\n[dim]Path: {self.current_dir}[/dim]",
            expand=False
        )
        table.add_column("Type", justify="center", style="cyan")
        table.add_column("File / Folder Name", justify="left", style="green")
        
        max_visible = 12
        start_idx = self.viewport_offset
        end_idx = min(len(self.items), start_idx + max_visible)
        
        for idx in range(start_idx, end_idx):
            item = self.items[idx]
            is_selected = (idx == self.cursor_idx)
            
            full_path = os.path.join(self.current_dir, item["name"])
            is_tagged = full_path in self.tagged_files
            
            item_type = "[DIR]" if item["is_dir"] else "[MP3]"
            name_str = f"* {item['name']}" if is_tagged else item["name"]
            
            if is_selected:
                table.add_row(
                    f"[bold yellow]>{item_type}[/bold yellow]",
                    f"[bold yellow]{name_str}[/bold yellow]"
                )
            elif is_tagged:
                table.add_row(
                    f"[bold green]{item_type}[/bold green]",
                    f"[bold green]{name_str}[/bold green]"
                )
            else:
                table.add_row(item_type, name_str)
                
        # Draw status panel
        legend = "[WASD] Nav | [Enter] Open/Play | [Space] Tag File | [P] Play Selected/All | [B] Back"
        if "TMUX" in os.environ:
            legend += " | [H] Home"
            
        panel = Panel(
            table,
            subtitle=f"[bold dim]{legend}[/bold dim]",
            expand=False
        )
        console.print(panel)

    def draw_graphical(self):
        if not self.fb_display:
            return
            
        self.fb_display.clear(20, 30, 45) # Deep retro blue background
        
        # 1. Draw Title Header (Height 32px)
        self.fb_display.draw_rect(0, 0, 320, 32, 10, 15, 25)
        self.fb_display.draw_string("CALCULINUX MP3 BROWSER", 10, 10, 1, 255, 215, 0)
        
        # 2. Draw Current Path Subheader (Height 20px)
        short_path = self.current_dir
        if len(short_path) > 35:
            short_path = "..." + short_path[-32:]
        self.fb_display.draw_string(short_path, 10, 40, 1, 0, 255, 255)
        
        # 3. Draw Items (Display area: y=65 to y=285, leaves room for 9 items at step 24px)
        max_visible = 9
        row_height = 24
        start_idx = self.viewport_offset
        end_idx = min(len(self.items), start_idx + max_visible)
        
        for idx in range(start_idx, end_idx):
            item = self.items[idx]
            is_selected = (idx == self.cursor_idx)
            
            full_path = os.path.join(self.current_dir, item["name"])
            is_tagged = full_path in self.tagged_files
            
            slot_y = 65 + (idx - start_idx) * row_height
            
            # Draw highlight background strip if selected
            if is_selected:
                self.fb_display.draw_rect(5, slot_y, 310, row_height - 2, 0, 128, 128) # Cyan select bar
                text_color = (0, 255, 0) if is_tagged else (255, 255, 255)
                icon_color = (255, 215, 0)
            else:
                text_color = (0, 200, 0) if is_tagged else (200, 200, 200)
                icon_color = (0, 200, 200) if item["is_dir"] else (150, 150, 150)
                
            # Draw type icons: [D] for Directory, [*] for Tagged, [M] for Music file
            if item["is_dir"]:
                icon_char = "D"
            elif is_tagged:
                icon_char = "*"
                icon_color = (0, 255, 0)
            else:
                icon_char = "M"
                
            self.fb_display.draw_string(f"[{icon_char}]", 10, slot_y + 4, 1, *icon_color)
            
            # Draw item name nicely truncated to prevent screen overflows
            display_name = item["name"]
            if len(display_name) > 30:
                display_name = display_name[:27] + "..."
                
            self.fb_display.draw_string(display_name, 45, slot_y + 4, 1, *text_color)
            
        # 4. Draw Footer Status Legend
        self.fb_display.draw_rect(0, 288, 320, 32, 10, 15, 25)
        legend_str = "WASD:NAV ENTER:PLAY SPACE:TAG P:PLAY"
        self.fb_display.draw_string(legend_str, 10, 298, 1, 200, 200, 200)
        
        self.fb_display.flush()

    def run_selected(self):
        if not self.items:
            return
            
        selected = self.items[self.cursor_idx]
        full_path = os.path.join(self.current_dir, selected["name"])
        
        if selected["is_dir"]:
            # Navigate inside the folder!
            self.current_dir = os.path.abspath(full_path)
            self.scan_directory()
        else:
            # Play the file!
            self.play_audio_file(full_path)

    def play_audio_file(self, file_path):
        self.play_playlist([file_path])

    def play_playlist(self, paths):
        if not paths:
            return

        # 1. Clear FB display cleanly so mpg123 can claim output terminal
        if self.fb_display:
            self.fb_display.clear(0, 0, 0)
            self.fb_display.flush()

        # 2. Re-apply standard stty canonical echoing so the user can control mpg123
        os.system("stty sane 2>/dev/null")
        
        total_songs = len(paths)
        for idx, path in enumerate(paths):
            console.clear()
            console.print(f"[bold green]Playing playlist ({idx + 1}/{total_songs})...[/bold green]\n")
            console.print(f"[bold cyan]File:[/bold cyan] {os.path.basename(path)}")
            console.print(f"[dim]Path: {path}[/dim]\n")
            
            console.print("[bold yellow]Interactive Controls:[/bold yellow]")
            console.print("  [s] or [Space] : Pause / Resume")
            console.print("  [d] : Skip to Next Song")
            console.print("  [f] : Fast-forward")
            console.print("  [+] or [-] : Volume up / down")
            console.print("  [q] : Quit entire playlist")
            console.print("\n----------------------------------------\n")
            
            if path.lower().endswith(".wma"):
                cmd = f"ffmpeg -loglevel quiet -i '{path}' -f mp3 - | mpg123 -C -a plug:bluealsa -"
            else:
                cmd = f"mpg123 -C -a plug:bluealsa '{path}'"
                
            try:
                res = subprocess.run(cmd, shell=True)
                if res.returncode in [130, -2, 2]: # standard shell abort codes
                    console.print("\n[yellow]Playlist playback aborted by user.[/yellow]")
                    time.sleep(1.0)
                    break
            except KeyboardInterrupt:
                console.print("\n[yellow]Playlist playback stopped by user.[/yellow]")
                time.sleep(1.0)
                break
            except Exception as e:
                console.print(f"[red]Error playing audio: {e}[/red]")
                time.sleep(2.0)

        # 3. Restore non-canonical raw terminal input on exit
        os.system("stty -icanon -echo 2>/dev/null")
        console.clear()

    def go_back(self):
        # Navigate up a folder level but never go beyond root_dir!
        if os.path.abspath(self.current_dir) != os.path.abspath(self.root_dir):
            self.current_dir = os.path.dirname(self.current_dir)
            self.scan_directory()

    def play(self):
        with RawTerminal():
            while True:
                if self.graphical_mode:
                    self.draw_graphical()
                else:
                    self.draw_terminal()
                    
                try:
                    key = get_key()
                except (KeyboardInterrupt, EOFError):
                    break
                    
                if key == "q":
                    break
                elif key == "h":
                    # Smart return home inside Tmux
                    if "TMUX" in os.environ:
                        subprocess.run("tmux select-window -t calculinux:Dashboard", shell=True)
                elif key == "w": # Up
                    if self.cursor_idx > 0:
                        self.cursor_idx -= 1
                        # Adjust scroll viewport
                        if self.cursor_idx < self.viewport_offset:
                            self.viewport_offset = self.cursor_idx
                elif key == "s": # Down
                    if self.cursor_idx < len(self.items) - 1:
                        self.cursor_idx += 1
                        # Adjust scroll viewport
                        max_visible = 9 if self.graphical_mode else 12
                        if self.cursor_idx >= self.viewport_offset + max_visible:
                            self.viewport_offset = self.cursor_idx - max_visible + 1
                elif key == " ":
                    # Tag / Untag selection!
                    if self.items:
                        selected = self.items[self.cursor_idx]
                        if selected["name"] != "..":
                            target_path = os.path.join(self.current_dir, selected["name"])
                            if selected["is_dir"]:
                                # Gather all playable files recursively under this directory
                                playable_files = []
                                for root, _, files in os.walk(target_path):
                                    for f in files:
                                        if f.lower().endswith((".mp3", ".wma")):
                                            playable_files.append(os.path.join(root, f))
                                if any(f in self.tagged_files for f in playable_files):
                                    # Untag all
                                    self.tagged_files.difference_update(playable_files)
                                else:
                                    # Tag all
                                    self.tagged_files.update(playable_files)
                            else:
                                # Toggle single file tag
                                if target_path in self.tagged_files:
                                    self.tagged_files.remove(target_path)
                                else:
                                    self.tagged_files.add(target_path)
                elif key in ["\r", "\n"]:
                    # Open folder or play single file immediately
                    self.run_selected()
                elif key == "p":
                    # Play selection or entire folder!
                    if self.tagged_files:
                        # Play all tagged files sorted alphabetically
                        self.play_playlist(sorted(list(self.tagged_files)))
                    else:
                        # Play all playable files in the current folder sorted alphabetically
                        current_playable = []
                        for item in self.items:
                            if not item["is_dir"]:
                                current_playable.append(os.path.join(self.current_dir, item["name"]))
                        self.play_playlist(sorted(current_playable))
                elif key in ["b", "a"]: # Back (b key or Left Arrow/A key)
                    self.go_back()
                    
        # Clean exit
        if self.fb_display:
            self.fb_display.clear(0, 0, 0)
            self.fb_display.flush()
            self.fb_display.close()
        console.clear()


def main():
    # Allow passing custom root music folder as argument
    root = "/home/root/music"
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        root = sys.argv[1]
        
    player = MP3Browser(root)
    player.play()


if __name__ == "__main__":
    main()