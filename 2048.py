import json
import os
import random
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
SCORE_FILE = "high_scores.json"

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


class Game2048:

    def __init__(self):
        self.grid = [[0] * 4 for _ in range(4)]
        self.score = 0
        self.high_score = self.load_high_score()
        self.has_won = False
        self.won_announced = False
        self.inverted_mode = False  # Default: Clear text on default background
        self.add_tile()
        self.add_tile()

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
            try:
                with open(SCORE_FILE, "w") as f:
                    json.dump({"high_score": self.high_score}, f)
            except Exception:
                pass

    def add_tile(self):
        empty = [
            (r, c)
            for r in range(4)
            for c in range(4)
            if self.grid[r][c] == 0
        ]
        if empty:
            r, c = random.choice(empty)
            self.grid[r][c] = 4 if random.random() < 0.1 else 2

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
            self.add_tile()
            self.save_high_score()

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

        subtitle_str = "[bold dim][Arrows/WASD] Move | [I] Invert | [Q] Quit[/bold dim]"
        if self.has_won and not self.won_announced:
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


def main():
    game = Game2048()
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
                break

            if key == "q":
                console.print("\n[yellow]Game exited.[/yellow]\n")
                break
            elif key == "i":
                game.inverted_mode = not game.inverted_mode
            elif key in ["w", "a", "s", "d"]:
                if game.has_won:
                    game.won_announced = True
                game.move(key)


if __name__ == "__main__":
    main()
