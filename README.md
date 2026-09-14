# CLI 2048 for Embedded Linux (Luckfox)

A lightweight, terminal-based implementation of the classic 2048 game built specifically for embedded Linux systems (like Luckfox Lyra) running stripped-down Python environments.

Now upgraded with game logging, interactive playback, step-jumping, active state takeover (grabbing control), step recall/undo, a persistent top-20 leaderboard, custom ASCII particle fireworks celebrations, and an auto-playing AI bot!

---

## Key Features

* **Zero Hardware/Library Overheads:** Requires no extra `pip` installs beyond `rich`.
* **Standard-Lib Terminal Input:** Captures instant keypresses using standard system `stty` utility rather than missing Python modules like `tty` or `termios`.
* **Step Recall / Undo (`R`):** Instantly undoes moves to restore the board, score, and state. Tracks the number of recalls used throughout the run.
* **Game Action Logging:** Outputs highly detailed, dated log files under the `logs/` directory containing grids, moves made, score shifts, and exact tile insertions.
* **Interactive Playback (`-p`):** Replays logs interactively. Supports pausing, step-by-step scrubbing, dynamic interval shifting, and multiplier speed scales (`<`/`>`).
* **Active Taking Over (`G`):** Press `G` at any point during playback to **grab control** of the past game and start playing live from that exact step (with full undo history kept!).
* **Step Jumping (`J`):** Instantly warp to any step number during playback to analyze or take over the game.
* **Auto-Play AI Bot Mode (`-t`):** Runs the game automatically using random movements. It simulates potential outcomes and dynamically filters out moves that make no effect to avoid infinite loops.
* **Top-20 Leaderboard:** Stores up to 20 top records in `high_scores.json` detailing Player Name, Score, Recalls, and Timestamp.
* **ASCII Fireworks "Video":** Plays a physics-based, gravity-simulated particle fireworks show in flashing console colors whenever a leaderboard high score is achieved.
* **Global Contextual Help Overlay (`H`/`?`):** Instantly displays a modal help screen tailored to your current mode (Active Play, Playback, or Bot Mode).

---

## How to Play

### Requirements
* **Python 3.8+**
* **`rich` module** (pre-installed on standard Luckfox image)
* Standard Linux `stty` utility (built into BusyBox/Linux)

### Running Options

| Command | Mode |
| :--- | :--- |
| **`python3 2048.py`** | Start a standard interactive game |
| **`python3 2048.py -p`** or **`--playback`** | Replay and manage recorded game logs |
| **`python3 2048.py -t1`** or **`--test1`** | Launch the Random AI Bot (moves randomly, avoids useless directions) |
| **`python3 2048.py -t2`** or **`--test2`** | Launch the Strategic AI Bot (Expectimax corner-locking AI) |
| **`python3 2048.py -t3`** or **`--test3`** (or **`-t`**) | Launch the Predictive AI Bot (Predictive Grandmaster AI with Survival Weighting) |
| **`python3 2048.py -s [port]`** or **`--server [port]`** | Start UDP Server Mode (default port 10000) for external network play |

---

## Game Controls

### 1. Active Gameplay Mode

| Key / Input | Action |
| :--- | :--- |
| **Arrow Keys** or **W / A / S / D** | Move tiles (Up, Left, Down, Right) |
| **`R`** | Recall (Undo) last step (increments recall counter) |
| **`I`** | Toggle display mode (High-Contrast Text ↔ Inverted Color Blocks) |
| **`H`** or **`?`** | Show modal shortcuts help screen |
| **`Q`** | Quit and save score to leaderboard (if qualified) |

### 2. Interactive Playback Replay Mode

| Key / Input | Action |
| :--- | :--- |
| **`Space`** | Pause / Resume automated replay |
| **`Left Arrow` / `Right Arrow`** | Step backward / forward frame-by-frame |
| **`Up Arrow` / `Down Arrow`** | Fine-tune frame interval duration (+/- 0.1s) |
| **`<` / `>`** (or **`,` / `.`**) | Halve / Double replay speed multiplier |
| **`J`** | Jump directly to any recorded step number |
| **`G`** | **Grab Control** (transition into live play from this frame!) |
| **`I`** | Toggle display mode |
| **`H`** or **`?`** | Show modal playback shortcuts help |
| **`Q`** | Exit playback |

### 3. Auto-Play Bot Mode

| Key / Input | Action |
| :--- | :--- |
| **`I`** | Toggle display mode |
| **`H`** or **`?`** | Show modal auto-play help |
| **`Q`** | Stop bot auto-play and exit |

---

## Technical Implementation Details

### 1. Game State Action Logging & Parsing
Every game automatically outputs detailed step-by-step logs into `logs/2048_YYYYMMDD_HHMMSS.log` using a structured, human-readable text block system:
```text
--- STEP 1 ---
Move: a
Score: 4
Grid:
4 0 0 0
2 0 0 0
0 0 0 0
0 0 2 0
Added Tile: 2 at (3, 2)
```
The playback system reads this log directory, formats files dynamically with localized timestamps, parses step frames sequentially into memory, and loads them into a fast, non-blocking rendering engine.

### 2. Recall (Undo) History Stack
The recall function utilizes a deep-copied history stack `self.history = []`. Before any move that changes the grid is applied, the game pushes the pre-move grid state, score, win flags, and metrics into the stack.
* Reverting pops the last dictionary, restores the state, increments `self.recall_count`, and appends a `Move: Recall` entry to the log file to maintain playback alignment.

### 3. Takeover (Control Grabbing) Mechanics
When `G` is pressed in playback, the engine suspends playback, extracts the sliced list of frames up to the current frame (`frames[:step_idx]`), and instantiates a fully interactive `Game2048` session using:
```python
Game2048.from_state(grid, score, history_frames)
```
This restores the exact visual board, score, and populates the undo history list with preceding steps—allowing players to undo moves that happened *before* they took control of the log!

### 4. Top-20 High Scores & Celebrations
The high score persistence handles JSON arrays gracefully. When the game ends, it checks if the player's score qualifies for the top 20. If so:
1. It suspends RawTerminal mode.
2. Runs `play_fireworks_video()`, generating floating ASCII particles utilizing simple vector mathematics and gravity simulation:
   * Particle position: $X_{new} = X + V_x$, $Y_{new} = Y + V_y$
   * Gravity factor: $V_{y, new} = V_y + 0.08$
3. Prompts the user for their name via standard `input()`.
4. Saves the details (name, score, recalls used, localized timestamp) into `high_scores.json`.
5. Prints a beautifully formatted Rich table.

### 5. Non-Blocking Event Replay Loop
To allow keyboard navigation (pausing, speeding up, changing options) during live playback or automated bot runs, the engine implements a portable, non-blocking input wrapper utilizing `select.select()` to poll standard input:
```python
rlist, _, _ = select.select([sys.stdin], [], [], timeout)
```
This guarantees high keyboard responsiveness on any BusyBox/Linux terminal without CPU-hogging busy-waiting.
