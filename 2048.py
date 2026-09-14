import datetime
import json
import math
import os
import random
import select
import socket
import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
SCORE_FILE = "high_scores.json"
LOG_DIR = "logs"

# High-contrast text foreground colors on default background (DEFAULT MODE)
FG_TILE_STYLES = {
    0: "dim white",
    2: "bold bright_blue",
    4: "bold bright_cyan",
    8: "bold bright_green",
    16: "bold bright_yellow",
    32: "bold bright_red",
    64: "bold bright_magenta",
    128: "bold yellow",
    256: "bold green",
    512: "bold cyan",
    1024: "bold red",
    2048: "bold magenta",
}

# Full background fill colors (INVERTED MODE)
BG_TILE_STYLES = {
    0: "dim black on grey30",
    2: "bold white on blue",
    4: "bold white on cyan",
    8: "bold black on green",
    16: "bold black on yellow",
    32: "bold white on red",
    64: "bold white on magenta",
    128: "bold black on bright_yellow",
    256: "bold black on bright_green",
    512: "bold black on bright_cyan",
    1024: "bold white on bright_red",
    2048: "bold white on bright_magenta",
}


class RawTerminal:
    """Disables line buffering and character echo using system stty."""

    def __enter__(self):
        self.old_settings = os.popen("stty -g 2>/dev/null").read().strip()
        os.system("stty -icanon -echo 2>/dev/null")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.old_settings:
            os.system(f"stty {self.old_settings} 2>/dev/null")


def get_key():
    """Reads a single keypress or arrow key escape sequence."""
    ch = sys.stdin.read(1)
    if ch == "\x1b":  # Arrow keys start with ESC sequence (\x1b)
        seq = sys.stdin.read(2)
        ch += seq
        if ch == "\x1b[A":
            return "w"  # Up
        elif ch == "\x1b[B":
            return "s"  # Down
        elif ch == "\x1b[C":
            return "d"  # Right
        elif ch == "\x1b[D":
            return "a"  # Left
    return ch.lower()


def show_help_screen(context="game"):
    console.clear()
    
    table = Table(title="❓ 2048 HELP & SHORTCUTS ❓", expand=False)
    table.add_column("Mode", justify="center", style="yellow")
    table.add_column("Shortcut", justify="center", style="cyan")
    table.add_column("Action", justify="left", style="green")
    
    if context in ["game", "all"]:
        table.add_row("Active Game", "Arrows / WASD", "Move tiles")
        table.add_row("Active Game", "R", "Recall (Undo) last step")
        table.add_row("Active Game", "I", "Toggle Inverted colors")
        table.add_row("Active Game", "H / ?", "Show this help screen")
        table.add_row("Active Game", "Q", "Quit game")
        
    if context in ["playback", "all"]:
        table.add_row("Replay/Playback", "Space", "Pause / Resume playback")
        table.add_row("Replay/Playback", "Left / Right", "Step backward / forward")
        table.add_row("Replay/Playback", "Up / Down", "Fine-tune speed (+/- 0.1s)")
        table.add_row("Replay/Playback", "< / > (or , / .)", "Halve / Double speed")
        table.add_row("Replay/Playback", "J", "Jump to step number")
        table.add_row("Replay/Playback", "G", "Grab control and start playing live!")
        table.add_row("Replay/Playback", "I", "Toggle Inverted colors")
        table.add_row("Replay/Playback", "H / ?", "Show this help screen")
        table.add_row("Replay/Playback", "Q", "Exit playback")
        
    if context in ["test", "all"]:
        table.add_row("Auto-Play Bot", "I", "Toggle Inverted colors")
        table.add_row("Auto-Play Bot", "H / ?", "Show this help screen")
        table.add_row("Auto-Play Bot", "Q", "Stop auto-play and exit")
        
    panel = Panel(
        table,
        subtitle="[bold yellow]Press any key to close help and return...[/bold yellow]",
        expand=False
    )
    console.print(panel)
    get_key()


class Game2048:

    def __init__(self, init_game=True):
        self.grid = [[0] * 4 for _ in range(4)]
        self.score = 0
        self.high_score = self.load_high_score()
        self.has_won = False
        self.won_announced = False
        self.inverted_mode = False  # Default: Clear text on default background
        
        # History and stats tracking
        self.history = []
        self.recall_count = 0
        self.step_count = 0
        
        if init_game:
            # Create dated log file
            os.makedirs(LOG_DIR, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file_path = os.path.join(LOG_DIR, f"2048_{timestamp}.log")
            
            self.add_tile()
            self.add_tile()
            self.log_step(move="Initial", added_tile_info=None)

    @classmethod
    def from_state(cls, grid, score, history_frames):
        game = cls(init_game=False)
        game.grid = [row[:] for row in grid]
        game.score = score
        game.history = []
        for frame in history_frames:
            game.history.append({
                "grid": [row[:] for row in frame["grid"]],
                "score": frame["score"],
                "has_won": any(2048 in row for row in frame["grid"]),
                "won_announced": False,
            })
        game.step_count = len(history_frames)
        
        os.makedirs(LOG_DIR, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        game.log_file_path = os.path.join(LOG_DIR, f"2048_{timestamp}_interactive.log")
        game.log_step(move="Grabbed Control", added_tile_info=None)
        return game

    def load_high_score(self):
        if os.path.exists(SCORE_FILE):
            try:
                with open(SCORE_FILE, "r") as f:
                    return json.load(f).get("high_score", 0)
            except Exception:
                return 0
        return 0

    def save_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score

    def add_tile(self):
        empty = [
            (r, c)
            for r in range(4)
            for c in range(4)
            if self.grid[r][c] == 0
        ]
        if empty:
            r, c = random.choice(empty)
            val = 4 if random.random() < 0.1 else 2
            self.grid[r][c] = val
            return val, r, c
        return None

    def log_step(self, move, added_tile_info=None):
        try:
            with open(self.log_file_path, "a") as f:
                f.write(f"--- STEP {self.step_count} ---\n")
                f.write(f"Move: {move}\n")
                f.write(f"Score: {self.score}\n")
                f.write("Grid:\n")
                for row in self.grid:
                    f.write(" ".join(str(val) for val in row) + "\n")
                added_str = "None"
                if added_tile_info:
                    val, r, c = added_tile_info
                    added_str = f"{val} at ({r}, {c})"
                f.write(f"Added Tile: {added_str}\n\n")
            self.step_count += 1
        except Exception:
            pass

    def recall_step(self):
        if self.history:
            state = self.history.pop()
            self.grid = state["grid"]
            self.score = state["score"]
            self.has_won = state["has_won"]
            self.won_announced = state["won_announced"]
            self.recall_count += 1
            self.log_step(move="Recall", added_tile_info=None)
            return True
        return False

    def _slide_left(self, row):
        new_row = [v for v in row if v != 0]
        score_gain = 0
        for i in range(len(new_row) - 1):
            if new_row[i] != 0 and new_row[i] == new_row[i + 1]:
                new_row[i] *= 2
                score_gain += new_row[i]
                new_row[i + 1] = 0
        new_row = [v for v in new_row if v != 0]
        new_row += [0] * (4 - len(new_row))
        return new_row, score_gain

    def move(self, direction):
        old_grid = [row[:] for row in self.grid]
        old_score = self.score

        if direction == "a":  # Left
            for i in range(4):
                self.grid[i], gain = self._slide_left(self.grid[i])
                self.score += gain

        elif direction == "d":  # Right
            for i in range(4):
                rev, gain = self._slide_left(self.grid[i][::-1])
                self.grid[i] = rev[::-1]
                self.score += gain

        elif direction == "w":  # Up
            cols = [list(c) for c in zip(*self.grid)]
            for i in range(4):
                cols[i], gain = self._slide_left(cols[i])
                self.score += gain
            self.grid = [list(c) for c in zip(*cols)]

        elif direction == "s":  # Down
            cols = [list(c) for c in zip(*self.grid)]
            for i in range(4):
                rev, gain = self._slide_left(cols[i][::-1])
                cols[i] = rev[::-1]
                self.score += gain
            self.grid = [list(c) for c in zip(*cols)]

        if self.grid != old_grid:
            state_copy = {
                "grid": old_grid,
                "score": old_score,
                "has_won": self.has_won,
                "won_announced": self.won_announced,
            }
            self.history.append(state_copy)
            
            added_tile_info = self.add_tile()
            self.save_high_score()
            self.log_step(move=direction, added_tile_info=added_tile_info)

        if (
            any(2048 in row for row in self.grid)
            and not self.won_announced
        ):
            self.has_won = True

    def render(self):
        console.clear()
        table = Table(
            show_header=False,
            show_edge=True,
            pad_edge=False,
            box=None,
            expand=False,
        )

        for _ in range(4):
            table.add_column(width=8, justify="center")

        active_styles = (
            BG_TILE_STYLES if self.inverted_mode else FG_TILE_STYLES
        )

        for row in self.grid:
            formatted_row = []
            for val in row:
                style = active_styles.get(val, "bold bright_white")
                text = f"{val}" if val != 0 else "."
                formatted_row.append(f"[{style}]  {text:^4}  [/{style}]")
            table.add_row(*formatted_row)

        subtitle_str = "[bold dim][Arrows/WASD] Move | [R] Recall | [I] Invert | [Q] Quit[/bold dim]"
        if getattr(self, "auto_play", False):
            subtitle_str = "[bold dim]🤖 AUTO-PLAY BOT MODE | [I] Invert | [Q] Stop[/bold dim]"
        elif self.has_won and not self.won_announced:
            subtitle_str = (
                "[bold bright_green]🏆 YOU REACHED 2048! [/bold bright_green]"
            )

        panel = Panel(
            table,
            title=f"[bold gold1] 2048 [/bold gold1] | Score: [bold cyan]{self.score}[/bold cyan] | Best: [bold green]{max(self.score, self.high_score)}[/bold green]",
            subtitle=subtitle_str,
            expand=False,
        )
        console.print(panel)

    def can_move(self):
        if any(0 in row for row in self.grid):
            return True
        for r in range(4):
            for c in range(4):
                if c < 3 and self.grid[r][c] == self.grid[r][c + 1]:
                    return True
                if r < 3 and self.grid[r][c] == self.grid[r + 1][c]:
                    return True
        return False

    def can_move_in_direction(self, direction):
        temp_grid = [row[:] for row in self.grid]
        
        if direction == "a":
            new_grid = []
            for i in range(4):
                row, _ = self._slide_left(temp_grid[i])
                new_grid.append(row)
            return new_grid != temp_grid
            
        elif direction == "d":
            new_grid = []
            for i in range(4):
                rev, _ = self._slide_left(temp_grid[i][::-1])
                new_grid.append(rev[::-1])
            return new_grid != temp_grid
            
        elif direction == "w":
            cols = [list(c) for c in zip(*temp_grid)]
            new_cols = []
            for i in range(4):
                col, _ = self._slide_left(cols[i])
                new_cols.append(col)
            new_grid = [list(c) for c in zip(*new_cols)]
            return new_grid != temp_grid
            
        elif direction == "s":
            cols = [list(c) for c in zip(*temp_grid)]
            new_cols = []
            for i in range(4):
                rev, _ = self._slide_left(cols[i][::-1])
                new_cols.append(rev[::-1])
            new_grid = [list(c) for c in zip(*new_cols)]
            return new_grid != temp_grid
            
        return False


def load_leaderboard():
    if os.path.exists(SCORE_FILE):
        try:
            with open(SCORE_FILE, "r") as f:
                data = json.load(f)
                scores = data.get("scores", [])
                high_score = data.get("high_score", 0)
                return scores, high_score
        except Exception:
            return [], 0
    return [], 0


def save_leaderboard(scores, high_score):
    try:
        with open(SCORE_FILE, "w") as f:
            json.dump({"high_score": high_score, "scores": scores}, f, indent=4)
    except Exception as e:
        console.print(f"[red]Error saving high scores: {e}[/red]")


def display_leaderboard():
    scores, historical_best = load_leaderboard()
    table = Table(title="🏆 2048 LEADERBOARD (TOP 20) 🏆", expand=False)
    table.add_column("Rank", justify="center", style="yellow")
    table.add_column("Player", justify="left", style="cyan")
    table.add_column("Score", justify="right", style="green")
    table.add_column("Recalls", justify="center", style="magenta")
    table.add_column("Date", justify="center", style="dim white")
    
    sorted_scores = sorted(scores, key=lambda x: x.get("score", 0), reverse=True)[:20]
    
    for idx, item in enumerate(sorted_scores):
        table.add_row(
            str(idx + 1),
            item.get("name", "Anonymous"),
            f"{item.get('score', 0):,}",
            str(item.get("recalls", 0)),
            item.get("date", "N/A")
        )
        
    if not sorted_scores:
        table.add_row("-", "No high scores yet!", "0", "0", "-")
        
    console.print(table)


def play_fireworks_video(text="NEW HIGH SCORE!"):
    width = 50
    height = 18
    colors = ["red", "green", "yellow", "blue", "magenta", "cyan", "white", "bright_yellow", "bright_cyan", "bright_red", "bright_green"]
    
    fireworks = [
        {"cx": 15, "cy": 16, "tx": 15, "ty": 5, "color": "bright_red", "particles": [], "state": "launch", "char": "^"},
        {"cx": 35, "cy": 16, "tx": 35, "ty": 6, "color": "bright_green", "particles": [], "state": "launch", "char": "^"},
    ]
    
    for frame in range(40):
        grid = [[" "] * width for _ in range(height)]
        
        for fw in fireworks:
            if fw["state"] == "launch":
                if fw["cy"] > fw["ty"]:
                    fw["cy"] -= 1
                    grid[fw["cy"]][fw["cx"]] = f"[bold {fw['color']}]{fw['char']}[/bold {fw['color']}]"
                else:
                    fw["state"] = "explode"
                    num_particles = 16
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


def check_and_save_leaderboard(score, recalls):
    scores, historical_best = load_leaderboard()
    
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
        
        text_video = "ALL-TIME HIGH SCORE!" if is_all_time_best else "NEW LEADERBOARD SCORE!"
        play_fireworks_video(text_video)
        
        console.print("\n[bold yellow]🏆 YOU ACHIEVED A LEADERBOARD HIGH SCORE! 🏆[/bold yellow]")
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
            "recalls": recalls,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        scores.append(new_entry)
        scores = sorted(scores, key=lambda x: x.get("score", 0), reverse=True)[:20]
        
        new_historical_best = max(score, historical_best)
        save_leaderboard(scores, new_historical_best)
        console.print("\n[bold green]High score saved successfully![/bold green]\n")
    else:
        console.print(f"\n[bold yellow]Your score: {score} (Recalls: {recalls}) did not make the top 20 leaderboard.[/bold yellow]\n")
        
    display_leaderboard()


def list_and_select_log():
    log_dir = "logs"
    if not os.path.exists(log_dir) or not os.listdir(log_dir):
        console.print("[red]No logs directory or log files found.[/red]")
        return None
        
    log_files = [f for f in os.listdir(log_dir) if f.startswith("2048_") and f.endswith(".log")]
    if not log_files:
        console.print("[red]No 2048 log files found in logs/ directory.[/red]")
        return None
        
    log_files.sort(reverse=True)
    
    table = Table(title="📁 SELECT GAME LOG TO PLAYBACK 📁", expand=False)
    table.add_column("No.", justify="center", style="yellow")
    table.add_column("File Name", justify="left", style="cyan")
    table.add_column("Date & Time", justify="center", style="green")
    
    for idx, filename in enumerate(log_files):
        try:
            parts = filename.split("_")
            date_part = parts[1]
            time_part = parts[2].split(".")[0]
            formatted_date = f"{date_part[0:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[0:2]}:{time_part[2:4]}:{time_part[4:6]}"
        except Exception:
            formatted_date = "N/A"
        table.add_row(str(idx + 1), filename, formatted_date)
        
    console.print(table)
    
    while True:
        try:
            choice = input("\nEnter log number to select (or 'q' to quit): ").strip().lower()
            if choice == 'q':
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(log_files):
                return os.path.join(log_dir, log_files[idx])
            else:
                console.print("[red]Invalid index. Please select a valid number.[/red]")
        except ValueError:
            console.print("[red]Please enter a valid number.[/red]")
        except (KeyboardInterrupt, EOFError):
            return None


def parse_log_file(file_path):
    frames = []
    try:
        with open(file_path, "r") as f:
            content = f.read()
    except Exception as e:
        console.print(f"[red]Error reading file {file_path}: {e}[/red]")
        return []
        
    steps = content.split("--- STEP ")
    for step in steps:
        if not step.strip():
            continue
        lines = [line.strip() for line in step.strip().split("\n") if line.strip()]
        if not lines:
            continue
            
        step_num_str = lines[0].split("---")[0].strip()
        try:
            step_num = int(step_num_str)
        except ValueError:
            continue
            
        move = "N/A"
        score = 0
        grid = []
        added_tile_info = "None"
        
        grid_lines_started = False
        grid_lines_count = 0
        
        for line in lines[1:]:
            if line.startswith("Move:"):
                move = line.split("Move:", 1)[1].strip()
            elif line.startswith("Score:"):
                try:
                    score = int(line.split("Score:", 1)[1].strip())
                except ValueError:
                    score = 0
            elif line.startswith("Grid:"):
                grid_lines_started = True
                grid_lines_count = 0
            elif grid_lines_started and grid_lines_count < 4:
                try:
                    row = [int(val) for val in line.split()]
                    if len(row) == 4:
                        grid.append(row)
                        grid_lines_count += 1
                except ValueError:
                    pass
            elif line.startswith("Added Tile:"):
                added_tile_info = line.split("Added Tile:", 1)[1].strip()
                
        if len(grid) == 4:
            frames.append({
                "step": step_num,
                "move": move,
                "score": score,
                "grid": grid,
                "added_tile": added_tile_info
            })
            
    frames.sort(key=lambda x: x["step"])
    return frames


def get_key_nonblocking(timeout):
    try:
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if rlist:
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r:
                    seq = sys.stdin.read(2)
                    ch += seq
                    if ch == "\x1b[A":
                        return "up"
                    elif ch == "\x1b[B":
                        return "down"
                    elif ch == "\x1b[C":
                        return "right"
                    elif ch == "\x1b[D":
                        return "left"
            return ch.lower()
    except Exception:
        pass
    return None


def render_playback(grid, score, step, total_steps, speed, move, added_tile, paused, inverted_mode):
    console.clear()
    table = Table(
        show_header=False,
        show_edge=True,
        pad_edge=False,
        box=None,
        expand=False,
    )

    for _ in range(4):
        table.add_column(width=8, justify="center")

    active_styles = BG_TILE_STYLES if inverted_mode else FG_TILE_STYLES

    for row in grid:
        formatted_row = []
        for val in row:
            style = active_styles.get(val, "bold bright_white")
            text = f"{val}" if val != 0 else "."
            formatted_row.append(f"[{style}]  {text:^4}  [/{style}]")
        table.add_row(*formatted_row)

    status = "[bold red]PAUSED[/bold red]" if paused else "[bold green]PLAYING[/bold green]"
    subtitle_str = f"Status: {status} | Interval: [cyan]{speed:.2f}s/f[/cyan] | Move: [green]{move}[/green] | Added: [magenta]{added_tile}[/magenta]\n"
    subtitle_str += "[bold dim][Space] Pause/Resume | [Left/Right] Step | [I] Invert | [</>] Speed x0.5/x2\n"
    subtitle_str += "[G] Grab Control | [J] Jump | [Q] Exit[/bold dim]"

    panel = Panel(
        table,
        title=f"[bold gold1] 📹 PLAYBACK 📹 [/bold gold1] | Step: [bold cyan]{step}/{total_steps}[/bold cyan] | Score: [bold cyan]{score}[/bold cyan]",
        subtitle=subtitle_str,
        expand=False,
    )
    console.print(panel)


def run_playback(frames):
    if not frames:
        console.print("[red]No frames to play.[/red]")
        return None
        
    step_idx = 0
    total_steps = len(frames)
    speed = 1.0
    paused = True  # Start paused so they can navigate/jump comfortably
    inverted_mode = False
    
    last_frame_time = time.time()
    
    while True:
        grab_control_game = None
        jump_requested = False
        
        with RawTerminal():
            while True:
                frame = frames[step_idx]
                render_playback(
                    grid=frame["grid"],
                    score=frame["score"],
                    step=step_idx + 1,
                    total_steps=total_steps,
                    speed=speed,
                    move=frame["move"],
                    added_tile=frame["added_tile"],
                    paused=paused,
                    inverted_mode=inverted_mode
                )
                
                if paused:
                    key = get_key_nonblocking(None)
                else:
                    now = time.time()
                    elapsed = now - last_frame_time
                    remaining = max(0.01, speed - elapsed)
                    key = get_key_nonblocking(remaining)
                    
                if key == "q":
                    return None
                elif key == "i":
                    inverted_mode = not inverted_mode
                elif key in ["h", "?"]:
                    show_help_screen("playback")
                    paused = True
                elif key == " ":
                    paused = not paused
                    if not paused:
                        last_frame_time = time.time()
                elif key == "up":
                    speed = max(0.01, speed - 0.1)
                elif key == "down":
                    speed = min(10.0, speed + 0.1)
                elif key in [">", "."]:
                    speed = max(0.01, speed / 2.0)
                elif key in ["<", ","]:
                    speed = min(10.0, speed * 2.0)
                elif key == "right":
                    if step_idx < total_steps - 1:
                        step_idx += 1
                        last_frame_time = time.time()
                elif key == "left":
                    if step_idx > 0:
                        step_idx -= 1
                        last_frame_time = time.time()
                elif key == "g":
                    history_upto = frames[:step_idx]
                    grab_control_game = Game2048.from_state(frame["grid"], frame["score"], history_upto)
                    break
                elif key == "j":
                    jump_requested = True
                    paused = True
                    break
                elif key is None and not paused:
                    if step_idx < total_steps - 1:
                        step_idx += 1
                        last_frame_time = time.time()
                    else:
                        paused = True
                        
            if grab_control_game is not None:
                return grab_control_game
                
        if jump_requested:
            console.print(f"\n[bold yellow]Jump to Step (1 - {total_steps}):[/bold yellow] ", end="")
            try:
                val = input().strip()
                if val.lower() == 'q':
                    pass
                else:
                    target_step = int(val)
                    if 1 <= target_step <= total_steps:
                        step_idx = target_step - 1
                        last_frame_time = time.time()
                    else:
                        console.print(f"[red]Step must be between 1 and {total_steps}.[/red]")
                        time.sleep(1.2)
            except ValueError:
                console.print("[red]Invalid step number.[/red]")
                time.sleep(1.2)
            except (KeyboardInterrupt, EOFError):
                pass


def simulate_move(grid, direction):
    temp_grid = [row[:] for row in grid]
    
    def slide_row_left(row):
        new_row = [v for v in row if v != 0]
        gain = 0
        for i in range(len(new_row) - 1):
            if new_row[i] != 0 and new_row[i] == new_row[i + 1]:
                new_row[i] *= 2
                gain += new_row[i]
                new_row[i + 1] = 0
        new_row = [v for v in new_row if v != 0]
        new_row += [0] * (4 - len(new_row))
        return new_row, gain

    score_gain = 0
    if direction == "a":
        for i in range(4):
            temp_grid[i], gain = slide_row_left(temp_grid[i])
            score_gain += gain
    elif direction == "d":
        for i in range(4):
            rev, gain = slide_row_left(temp_grid[i][::-1])
            temp_grid[i] = rev[::-1]
            score_gain += gain
    elif direction == "w":
        cols = [list(c) for c in zip(*temp_grid)]
        for i in range(4):
            cols[i], gain = slide_row_left(cols[i])
            score_gain += gain
        temp_grid = [list(c) for c in zip(*cols)]
    elif direction == "s":
        cols = [list(c) for c in zip(*temp_grid)]
        for i in range(4):
            rev, gain = slide_row_left(cols[i][::-1])
            cols[i] = rev[::-1]
            score_gain += gain
        temp_grid = [list(c) for c in zip(*cols)]
        
    changed = (temp_grid != grid)
    return temp_grid, changed, score_gain


def evaluate_grid(grid):
    W_MATRIX = [
        [3,  2,  1,  0],
        [4,  5,  6,  7],
        [11, 10, 9,  8],
        [12, 13, 14, 15]
    ]
    
    monotonicity_score = 0
    max_tile = 0
    max_r, max_c = 0, 0
    empty_cells = 0
    
    for r in range(4):
        for c in range(4):
            val = grid[r][c]
            if val > max_tile:
                max_tile = val
                max_r, max_c = r, c
            if val == 0:
                empty_cells += 1
            else:
                power = math.log2(val)
                weight = 4 ** W_MATRIX[r][c]
                monotonicity_score += power * weight
                
    score = monotonicity_score
    
    if max_r == 3 and max_c == 3:
        score += (4 ** 16) * math.log2(max_tile)
    else:
        score -= (4 ** 17) * math.log2(max_tile)
        
    bottom_row_full = all(grid[3][c] != 0 for c in range(4))
    if bottom_row_full:
        score += 4 ** 14
    else:
        empty_bottom = sum(1 for c in range(4) if grid[3][c] == 0)
        score -= (4 ** 14) * empty_bottom
        
    smoothness = 0
    for r in range(4):
        for c in range(4):
            if grid[r][c] != 0:
                if c < 3 and grid[r][c] == grid[r][c+1]:
                    smoothness += math.log2(grid[r][c]) * (4 ** W_MATRIX[r][c])
                if r < 3 and grid[r][c] == grid[r+1][c]:
                    smoothness += math.log2(grid[r][c]) * (4 ** W_MATRIX[r][c])
    score += smoothness
    
    score += empty_cells * (4 ** 8)
    return score


def expectimax(grid, depth, is_player):
    # Base case: depth reached or no empty cells/cannot move
    empty_cells = [(r, c) for r in range(4) for c in range(4) if grid[r][c] == 0]
    
    # Simple check if player can move in grid
    can_move = False
    for d in ["s", "d", "a", "w"]:
        _, changed, _ = simulate_move(grid, d)
        if changed:
            can_move = True
            break
            
    if depth == 0 or (is_player and not can_move):
        return evaluate_grid(grid)
        
    if is_player:
        best_score = -float('inf')
        for d in ["s", "d", "a", "w"]:
            next_grid, changed, _ = simulate_move(grid, d)
            if changed:
                score = expectimax(next_grid, depth - 1, False)
                if d in ["a", "w"]:
                    score -= (4 ** 14)
                best_score = max(best_score, score)
        return best_score
    else:
        if not empty_cells:
            return evaluate_grid(grid)
            
        total_score = 0
        for r, c in empty_cells:
            grid[r][c] = 2
            score_2 = expectimax(grid, depth - 1, True)
            grid[r][c] = 4
            score_4 = expectimax(grid, depth - 1, True)
            grid[r][c] = 0
            total_score += 0.9 * score_2 + 0.1 * score_4
            
        return total_score / len(empty_cells)


def run_random_test_mode():
    game = Game2048()
    game.auto_play = True
    
    with RawTerminal():
        while True:
            game.render()
            
            if not game.can_move():
                console.print(
                    "\n[bold red]💀 GAME OVER! No more valid moves.[/bold red]"
                )
                console.print(
                    f"[bold yellow]Final Score: {game.score} | Best: {game.high_score}[/bold yellow]\n"
                )
                break
                
            key = get_key_nonblocking(0.15)
            if key == "q":
                console.print("\n[yellow]Auto-play stopped by user.[/yellow]\n")
                break
            elif key == "i":
                game.inverted_mode = not game.inverted_mode
            elif key in ["h", "?"]:
                show_help_screen("test")
                
            valid_dirs = [d for d in ["w", "a", "s", "d"] if game.can_move_in_direction(d)]
            if valid_dirs:
                move = random.choice(valid_dirs)
                if game.has_won:
                    game.won_announced = True
                game.move(move)
            else:
                break
                
    check_and_save_leaderboard(game.score, game.recall_count)


def run_strategic_test_mode():
    game = Game2048()
    game.auto_play = True
    
    with RawTerminal():
        while True:
            game.render()
            
            if not game.can_move():
                console.print(
                    "\n[bold red]💀 GAME OVER! No more valid moves.[/bold red]"
                )
                console.print(
                    f"[bold yellow]Final Score: {game.score} | Best: {game.high_score}[/bold yellow]\n"
                )
                break
                
            key = get_key_nonblocking(0.1)
            if key == "q":
                console.print("\n[yellow]Auto-play stopped by user.[/yellow]\n")
                break
            elif key == "i":
                game.inverted_mode = not game.inverted_mode
            elif key in ["h", "?"]:
                show_help_screen("test")
                
            empty_count = sum(1 for r in range(4) for c in range(4) if game.grid[r][c] == 0)
            depth = 3 if empty_count < 6 else 2
            
            best_move = None
            best_score = -float('inf')
            
            for d in ["s", "d", "a", "w"]:
                next_grid, changed, _ = simulate_move(game.grid, d)
                if changed:
                    score = expectimax(next_grid, depth - 1, False)
                    if d in ["a", "w"]:
                        score -= (4 ** 14)
                    if score > best_score:
                        best_score = score
                        best_move = d
                        
            if best_move is not None:
                if game.has_won:
                    game.won_announced = True
                game.move(best_move)
            else:
                break
                
    check_and_save_leaderboard(game.score, game.recall_count)


def calculate_survival_probability(grid):
    empty_cells = [(r, c) for r in range(4) for c in range(4) if grid[r][c] == 0]
    if not empty_cells:
        for d in ["s", "d", "a", "w"]:
            _, changed, _ = simulate_move(grid, d)
            if changed:
                return 1.0
        return 0.0
        
    safe_spawns = 0
    total_spawns = len(empty_cells) * 2
    
    for r, c in empty_cells:
        for spawn_val in [2, 4]:
            grid[r][c] = spawn_val
            has_move = False
            for d in ["s", "d", "a", "w"]:
                _, changed, _ = simulate_move(grid, d)
                if changed:
                    has_move = True
                    break
            if has_move:
                safe_spawns += 1
            grid[r][c] = 0
            
    return safe_spawns / total_spawns


def evaluate_grid_t3(grid):
    W_MATRIX = [
        [3,  2,  1,  0],
        [4,  5,  6,  7],
        [11, 10, 9,  8],
        [12, 13, 14, 15]
    ]
    
    monotonicity_score = 0
    max_tile = 0
    max_r, max_c = 0, 0
    empty_cells = 0
    
    for r in range(4):
        for c in range(4):
            val = grid[r][c]
            if val > max_tile:
                max_tile = val
                max_r, max_c = r, c
            if val == 0:
                empty_cells += 1
            else:
                power = math.log2(val)
                weight = 4 ** W_MATRIX[r][c]
                monotonicity_score += power * weight
                
    score = monotonicity_score
    
    if max_r == 3 and max_c == 3:
        score += (4 ** 16) * math.log2(max_tile)
    else:
        score -= (4 ** 17) * math.log2(max_tile)
        
    bottom_row_full = all(grid[3][c] != 0 for c in range(4))
    if bottom_row_full:
        score += 4 ** 14
    else:
        empty_bottom = sum(1 for c in range(4) if grid[3][c] == 0)
        score -= (4 ** 14) * empty_bottom
        
    smoothness = 0
    for r in range(4):
        for c in range(4):
            if grid[r][c] != 0:
                if c < 3 and grid[r][c] == grid[r][c+1]:
                    smoothness += math.log2(grid[r][c]) * (4 ** W_MATRIX[r][c])
                if r < 3 and grid[r][c] == grid[r+1][c]:
                    smoothness += math.log2(grid[r][c]) * (4 ** W_MATRIX[r][c])
    score += smoothness
    
    score += empty_cells * (4 ** 9)
    return score


def expectimax_t3(grid, depth, is_player):
    empty_cells = [(r, c) for r in range(4) for c in range(4) if grid[r][c] == 0]
    
    valid_moves = []
    for d in ["s", "d", "a", "w"]:
        _, changed, _ = simulate_move(grid, d)
        if changed:
            valid_moves.append(d)
            
    if is_player and not valid_moves:
        return -10**18 + (depth * 10**12)
        
    if depth == 0:
        return evaluate_grid_t3(grid)
        
    if is_player:
        best_score = -float('inf')
        for d in valid_moves:
            next_grid, _, _ = simulate_move(grid, d)
            score = expectimax_t3(next_grid, depth - 1, False)
            if d in ["a", "w"]:
                score -= (4 ** 14)
            best_score = max(best_score, score)
        return best_score
    else:
        if not empty_cells:
            return evaluate_grid_t3(grid)
            
        total_score = 0
        for r, c in empty_cells:
            grid[r][c] = 2
            score_2 = expectimax_t3(grid, depth - 1, True)
            grid[r][c] = 4
            score_4 = expectimax_t3(grid, depth - 1, True)
            grid[r][c] = 0
            total_score += 0.9 * score_2 + 0.1 * score_4
            
        return total_score / len(empty_cells)


def run_predictive_test_mode():
    game = Game2048()
    game.auto_play = True
    
    with RawTerminal():
        while True:
            game.render()
            
            if not game.can_move():
                console.print(
                    "\n[bold red]💀 GAME OVER! No more valid moves.[/bold red]"
                )
                console.print(
                    f"[bold yellow]Final Score: {game.score} | Best: {game.high_score}[/bold yellow]\n"
                )
                break
                
            key = get_key_nonblocking(0.1)
            if key == "q":
                console.print("\n[yellow]Auto-play stopped by user.[/yellow]\n")
                break
            elif key == "i":
                game.inverted_mode = not game.inverted_mode
            elif key in ["h", "?"]:
                show_help_screen("test")
                
            empty_count = sum(1 for r in range(4) for c in range(4) if game.grid[r][c] == 0)
            depth = 4 if empty_count < 5 else (3 if empty_count < 9 else 2)
            
            best_move = None
            best_score = -float('inf')
            
            for d in ["s", "d", "a", "w"]:
                next_grid, changed, _ = simulate_move(game.grid, d)
                if changed:
                    score = expectimax_t3(next_grid, depth - 1, False)
                    survival_prob = calculate_survival_probability(next_grid)
                    
                    if survival_prob < 1.0:
                        score -= (1.0 - survival_prob) * (10 ** 16)
                    else:
                        score += (4 ** 12)
                        
                    if d in ["a", "w"]:
                        score -= (4 ** 14)
                        
                    if score > best_score:
                        best_score = score
                        best_move = d
                        
            if best_move is not None:
                if game.has_won:
                    game.won_announced = True
                game.move(best_move)
            else:
                break
                
    check_and_save_leaderboard(game.score, game.recall_count)


def run_udp_server(port=10000):
    game = Game2048()
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        server_socket.bind(("0.0.0.0", port))
    except Exception as e:
        console.print(f"[red]Error binding UDP socket to port {port}: {e}[/red]")
        return
        
    console.print(f"[green]UDP Server listening on 0.0.0.0:{port}...[/green]")
    console.print("[dim]Press [Q] on keyboard to stop server.[/dim]")
    time.sleep(1.0)
    
    with RawTerminal():
        while True:
            game.render()
            
            game_over = not game.can_move()
            if game_over:
                console.print("\n[bold red]💀 GAME OVER! No more valid moves.[/bold red]\n")
                
            rlist, _, _ = select.select([sys.stdin, server_socket], [], [])
            
            for source in rlist:
                if source == sys.stdin:
                    key = sys.stdin.read(1)
                    if key.lower() == "q":
                        console.print("\n[yellow]UDP Server stopped by user.[/yellow]\n")
                        server_socket.close()
                        return
                    elif key.lower() == "i":
                        game.inverted_mode = not game.inverted_mode
                elif source == server_socket:
                    data, addr = server_socket.recvfrom(1024)
                    msg = data.decode("utf-8").strip().lower()
                    
                    if msg in ["w", "up"]:
                        if not game_over:
                            if game.has_won:
                                game.won_announced = True
                            game.move("w")
                    elif msg in ["s", "down"]:
                        if not game_over:
                            if game.has_won:
                                game.won_announced = True
                            game.move("s")
                    elif msg in ["a", "left"]:
                        if not game_over:
                            if game.has_won:
                                game.won_announced = True
                            game.move("a")
                    elif msg in ["d", "right"]:
                        if not game_over:
                            if game.has_won:
                                game.won_announced = True
                            game.move("d")
                    elif msg in ["r", "undo"]:
                        game.recall_step()
                    elif msg in ["i", "invert"]:
                        game.inverted_mode = not game.inverted_mode
                    elif msg in ["q", "quit"]:
                        console.print(f"\n[yellow]UDP Client {addr} requested quit.[/yellow]\n")
                        server_socket.close()
                        return
                        
                    reply = {
                        "grid": game.grid,
                        "score": game.score,
                        "high_score": game.high_score,
                        "has_won": game.has_won,
                        "game_over": not game.can_move(),
                        "recall_count": game.recall_count
                    }
                    try:
                        server_socket.sendto(json.dumps(reply).encode("utf-8"), addr)
                    except Exception:
                        pass


def run_active_game(game):
    aborted = False
    with RawTerminal():
        while True:
            game.render()

            if not game.can_move():
                console.print(
                    "\n[bold red]💀 GAME OVER! No more valid moves.[/bold red]"
                )
                console.print(
                    f"[bold yellow]Final Score: {game.score} | Best: {game.high_score}[/bold yellow]\n"
                )
                break

            try:
                key = get_key()
            except (KeyboardInterrupt, EOFError):
                aborted = True
                break

            if key == "q":
                console.print("\n[yellow]Game exited.[/yellow]\n")
                break
            elif key == "i":
                game.inverted_mode = not game.inverted_mode
            elif key == "r":
                game.recall_step()
            elif key in ["h", "?"]:
                show_help_screen("game")
            elif key in ["w", "a", "s", "d"]:
                if game.has_won:
                    game.won_announced = True
                game.move(key)

    if not aborted:
        check_and_save_leaderboard(game.score, game.recall_count)


def main():
    if "-s" in sys.argv or "--server" in sys.argv:
        port = 10000
        idx = sys.argv.index("-s") if "-s" in sys.argv else sys.argv.index("--server")
        if idx + 1 < len(sys.argv):
            try:
                port = int(sys.argv[idx + 1])
            except ValueError:
                console.print(f"[yellow]Invalid port number '{sys.argv[idx + 1]}'. Using default 10000.[/yellow]")
        run_udp_server(port)
        return
    elif len(sys.argv) > 1 and sys.argv[1] in ["-p", "--playback"]:
        log_file = list_and_select_log()
        if log_file:
            frames = parse_log_file(log_file)
            if frames:
                game = run_playback(frames)
                if game is not None:
                    run_active_game(game)
        return
    elif len(sys.argv) > 1 and sys.argv[1] in ["-t1", "--test1"]:
        run_random_test_mode()
        return
    elif len(sys.argv) > 1 and sys.argv[1] in ["-t2", "--test2"]:
        run_strategic_test_mode()
        return
    elif len(sys.argv) > 1 and sys.argv[1] in ["-t3", "--test3", "-t", "--test"]:
        run_predictive_test_mode()
        return

    game = Game2048()
    run_active_game(game)


if __name__ == "__main__":
    main()
