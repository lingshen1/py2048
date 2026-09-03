# CLI 2048 for Embedded Linux (Luckfox)

A lightweight, terminal-based implementation of the classic 2048 game built specifically for embedded Linux systems (like Luckfox Lyra) running stripped-down Python environments.

---

## Key Features

* **Zero Hardware/Library Overheads:** Requires no extra `pip` installs beyond `rich`.
* **Standard-Lib Terminal Input:** Captures instant keypresses using system `stty` commands rather than missing Python modules like `tty` or `termios`.
* **LCD Screen Optimization:** Features two rendering modes (High-contrast text vs. Full-color background blocks) optimized for small SPI/I2C LCD displays.
* **Arrow Key & WASD Support:** Intercepts standard ANSI escape sequences for seamless directional control without requiring the **Enter** key.
* **Persistent High Scores:** Automatically saves and loads your highest score locally to `high_scores.json`.
* **Full Game State Tracking:** Detects victory (2048 tile reached) with option to continue, and handles game-over states when no valid moves remain.

---

## How to Play

### Requirements
* **Python 3.8+**
* **`rich` module** (pre-installed on standard Luckfox image)
* Standard Linux `stty` utility (built into BusyBox/Linux)

### Run the Game

```bash
python3 2048.py
```

### Controls

| Key / Input | Action |
| :--- | :--- |
| **Arrow Keys** or **W / A / S / D** | Move tiles (Up, Left, Down, Right) |
| **`I`** | Toggle display mode (High-Contrast Text ↔ Inverted Color Blocks) |
| **`Q`** | Quit game |

---

## Technical Implementation Details

### 1. Terminal Handling without `tty` / `termios`
Embedded Python distributions often strip out C-extension standard library modules like `tty` and `termios` to save flash storage. To achieve single-character keypresses without needing **Enter**:

* **`RawTerminal` Context Manager:** Uses `os.system("stty -icanon -echo")` to put the terminal into non-canonical (raw) mode and disable character echo. Upon exiting, it restores the previous terminal state saved via `stty -g`.
* **`get_key()` Interceptor:** Reads single bytes directly from `sys.stdin`. When an escape byte (`\x1b`) is detected, it reads the subsequent 2 bytes to match ANSI escape sequences:
  * `\x1b[A` → Up (`w`)
  * `\x1b[B` → Down (`s`)
  * `\x1b[C` → Right (`d`)
  * `\x1b[D` → Left (`a`)

### 2. Matrix Transformations & Sliding Algorithm
All movement logic is reduced to a single, pure 1D function: `_slide_left()`. Any directional move transforms the grid matrix into a left-slide operation, applies the merge logic, and transforms it back:

* **Left (`A`):** Applied directly to each row.
* **Right (`D`):** Reverses each row → Slides Left → Reverses row back.
* **Up (`W`):** Transposes matrix (`zip(*grid)`) → Slides Left → Transposes back.
* **Down (`S`):** Transposes matrix → Reverses each column → Slides Left → Reverses back → Transposes back.

```text
Original Grid            Transposed (Up/Down)         Reversed (Right/Down)
[ 2 , 0 , 0 , 0 ]       [ 2 , 0 , 2 , 4 ]            [ 0 , 0 , 0 , 2 ]
[ 8 , 0 , 0 , 0 ]  ==>  [ 0 , 0 , 0 , 0 ]     ==>    [ 0 , 0 , 0 , 8 ]
[ 2 , 0 , 2 , 0 ]       [ 0 , 0 , 2 , 0 ]            [ 0 , 2 , 0 , 2 ]
[ 4 , 0 , 0 , 0 ]       [ 0 , 0 , 0 , 0 ]            [ 0 , 0 , 0 , 4 ]
```

### 3. Display Rendering & Dual Contrast Modes
The game interface uses `rich.table.Table` nested inside `rich.panel.Panel`. On small embedded screens, solid background fills often blur together or wash out:

* **Default Mode (`FG_TILE_STYLES`):** Applies bright foreground text colors on the terminal's native background, preserving pixel clarity on small LCD displays.
* **Inverted Mode (`BG_TILE_STYLES`):** Toggled via `I`, uses full background block colors matching the classic 2048 layout.

### 4. Score Persistence
Scores are automatically verified after every valid move. If `score > high_score`, the updated value is saved to `high_scores.json`:

```json
{
  "high_score": 2048
}
```

If the file is deleted or corrupt, the game safely catches the exception and resets the local high score counter to `0`.
