# CLI 2048 for Embedded Linux (Luckfox)

**Version:** `v3.0.0`  
**Author:** `Ling Shen`  

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
* **Calculinux Framebuffer Graphics Display (`-g`):** Auto-detects the Calculinux 320x320 display and draws high-performance, double-buffered full-color graphics directly onto `/dev/fb0` using a custom pixel-art font and native colors. Can be combined with other modes (e.g. Server, Playback, or Bot Mode).

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
| **`-g`** or **`--graph`** | *(Append to any command)* Enable raw framebuffer full-color graphical display on Calculinux (/dev/fb0) |

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

### 4. Top-20 High Scores, Graphical Video & Audio Celebrations
The high score persistence handles JSON leaderboard arrays gracefully. When the game ends, it checks if the player's score qualifies for the top 20. If so:
1. It suspends RawTerminal mode.
2. Plays a dynamic, colorful celebration video:
   * **In Text Mode**: Runs `play_fireworks_video()`, generating floating ASCII particles using simple vector mathematics and gravity simulation:
     * Particle position: $X_{new} = X + V_x$, $Y_{new} = Y + V_y$
     * Gravity factor: $V_{y, new} = V_y + 0.08$
   * **In Graphical Mode (`-g`)**: Runs `play_graphical_fireworks_video()`, generating floating, full-color dynamic pixel fireworks directly on the `/dev/fb0` framebuffer backbuffer and flushing it smoothly.
3. **Adaptive Audio Melodies**: If an active sound driver or ALSA device (like onboard audio, connected USB card, or a paired Bluetooth headset) is detected, the game mathematically synthesizes George Frideric Handel's famous *"See, the conqu'ring hero comes!"* victory chorus in pure Python (8-bit, 8kHz mono raw PCM) and pipes it directly to `aplay` in the background in perfect sync with the fireworks!
4. Prompts the user for their name via standard `input()`.
5. Saves the details (name, score, recalls used, localized timestamp) into `high_scores.json`.
6. Prints a beautifully formatted Rich table.

### 5. Non-Blocking Event Replay Loop
To allow keyboard navigation (pausing, speeding up, changing options) during live playback or automated bot runs, the engine implements a portable, non-blocking input wrapper utilizing `select.select()` to poll standard input:
```python
rlist, _, _ = select.select([sys.stdin], [], [], timeout)
```
This guarantees high keyboard responsiveness on any BusyBox/Linux terminal without CPU-hogging busy-waiting.

---

## Trainable Neural Network UDP Bot Client (`bot_client.py`)

A fully self-contained external Python client (`bot_client.py`) is provided that plays the game over UDP by connecting to the 2048 game server.

### Features
* **Xavier-Initialized Neural Network**: Built entirely using the standard Python library (no TensorFlow/PyTorch required!). Implements forward propagation, ReLU activation, backpropagation, and stochastic gradient descent (SGD).
* **Heuristic-Guided Policy (AlphaGo-Style)**: Pairs the Neural Network with the expert-grade heuristics of `-t3` (corner-locking, monotonicity, full bottom-row) to guide the search.
* **Temporal Difference (TD) Learning**: Trains the value network in real-time. On every action, it computes the reinforcement learning TD-target:
  $$Target = Reward + \gamma \cdot Value(S')$$
  and backpropagates the loss error to optimize the state-value weights.
* **Weights Persistence**: Automatically saves and loads trained weights from `bot_weights.json`.

### How to Use the Bot Client

1. **Start the 2048 UDP Game Server** in one terminal:
   ```bash
   python3 2048.py -s
   ```

2. **Run the Bot Client to Play** in another terminal:
   ```bash
   python3 bot_client.py --play
   ```

3. **Train the Neural Network** for a specified number of games (e.g., 50 games):
   ```bash
   python3 bot_client.py --train 50
   ```

---

## Step-by-Step Training & UDP Network Integration Guide

To allow external code to interact with and train on the 2048 game, the system is designed around a lightweight, multiplexed network protocol.

### 1. The UDP Server Command-Action Protocol
The game server (`2048.py -s`) runs a high-performance UDP server on `0.0.0.0:10000` (by default). The network interface uses simple UTF-8 text command packets and replies instantly with a JSON-serialized game state dictionary.

#### Available Client Commands:
* **`reset` / `restart`**: Instantly clears the game board, instantiates a fresh game state, and clears `game_over` status. Useful to reset between training epochs.
* **`w` / `up`**: Slide Up.
* **`s` / `down`**: Slide Down.
* **`a` / `left`**: Slide Left.
* **`d` / `right`**: Slide Right.
* **`r` / `undo`**: Revert to previous step (Undo).
* **`i` / `invert`**: Toggle inverted console color blocks.
* **`q` / `quit`**: Gracefully disconnect the socket and close the game server.
* **`state` / `get`**: Simply request the current game state without making a move.

#### Server JSON Reply Format:
On receiving any of the above commands, the server responds to the client's socket address with a JSON payload:
```json
{
    "grid": [[0, 2, 0, 0], [4, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
    "score": 8,
    "high_score": 1024,
    "has_won": false,
    "game_over": false,
    "recall_count": 0
}
```

---

### 2. Step-by-Step Training Procedure
Below is the precise procedure for booting up the learning environment and executing reinforcement learning training:

#### Step 1: Fire up the Training Arena (Terminal 1)
Start the UDP game server. This opens the network socket and draws the console screen:
```bash
python3 2048.py -s
```
*The server begins listening. You can press `Q` on Terminal 1's keyboard at any point to stop it.*

#### Step 2: Trigger the Learning Loop (Terminal 2)
In another terminal window, start the training client to play and train the neural network over 50 consecutive games:
```bash
python3 bot_client.py --train 50
```

#### Step 3: Watch the Reinforcement Learning in Action
* **How the Client Thinks**:
  1. At the start of each game, the client sends a `reset` command over UDP to Terminal 1 to ensure a clean board.
  2. For every turn, the client reads the grid, extracts normalized log2 features, and runs Expectimax search lookahead. It evaluates final branches by summing the expert heuristics of `-t3` and its own Neural Network's value prediction.
  3. It sends the best movement key (`w`/`a`/`s`/`d`) to the UDP server.
  4. It receives the resulting grid. It calculates the normalized reward:
     $$Reward = \frac{\Delta \text{Score}}{100.0}$$
  5. It calculates the **Temporal Difference (TD) target** ($Target = Reward + \gamma \cdot Value(S')$) and runs a backward pass to perform stochastic gradient descent (SGD) on the network's synapses ($w_1, b1, w2, b2$).
  6. When the game ends, the client prints the completed score and automatically loops back to send a `reset` for the next game.
* **What you see on screen**:
  * **On Terminal 2**: You see active logs of completed training games:
    `Game 1/50 starting... Completed! Score: 1024 | Moves: 92`
  * **On Terminal 1**: You can watch the game board flashing and updating live at hundreds of actions per second as the bot runs through its training games!

#### Step 4: Weights Saving & Evaluation
* Once all 50 games are completed, the client calculates rolling statistics (average score, highest score) and dumps the fully optimized synaptic weights into `bot_weights.json`.
* To evaluate the learned weights, run the bot client in play mode:
  ```bash
  python3 bot_client.py --play
  ```
  This loads your saved weights and lets you watch the trained neural network play a live, step-by-step game on your server screen!

---

## How the AI Bot Thinks: The Three Core Weights

The grandmaster performance of the `-t3` and `bot_client.py` agents lies in **three distinct layers of mathematical weighting** working in synergy:

### 1. Heuristic Board Weights (The "Symmetric Flow" Guide)
The core heuristic weights are structured as a snake-like gradient wrapping upwards from the bottom-right corner:
```python
W_MATRIX = [
    [3,  2,  1,  0],   # Row 0
    [4,  5,  6,  7],   # Row 1
    [11, 10, 9,  8],   # Row 2
    [12, 13, 14, 15]   # Row 3 (Bottom)
]
```

* **Exponential Scaling ($4^W$):** Instead of multiplying a tile value directly, the bot multiplies the logarithm of the tile value by $4^{\text{weight\_index}}$. For example, a $1024$ tile at `(3, 3)` (weight 15) is scored as $10 \times 4^{15} \approx 10.7\text{ Billion}$, while sliding to `(3, 2)` (weight 14) drops its score to $10 \times 4^{14} \approx 2.6\text{ Billion}$.
* **Strategic Utility:** This massive exponential drop-off creates an intense "gravitational pull" that forces the largest numbers to stay strictly locked in the bottom-right corner. It sets up a monotonic descending slope where smaller tiles naturally flow down the "snake slide" into larger ones, creating effortless, automatic merge cascades.

### 2. Survival Probability Weights (The "Lookahead Safety" Shield)
A common failure for basic 2048 bots is greediness—making a high-scoring merge that collapses empty spaces and locks the board on the very next turn (sudden death). The predictive bot solves this by calculating the **Survival Probability ($P_{\text{survival}}$)** of the board *after* a prospective move:

$$P_{\text{survival}} = \frac{\text{Number of safe spawns (leaving } \ge 1 \text{ valid move)}}{\text{Total possible random spawns (every empty cell spawning a 2 or 4)}}$$

* **Risk-Adjusted Penalty:** If a move has even a tiny $10\%$ chance of causing a sudden game-over on the next turn ($P_{\text{survival}} = 0.90$), the bot hits the move's score with a massive penalty:
  $$\text{Penalty} = (1.0 - P_{\text{survival}}) \times 10^{16} = 0.1 \times 10^{16}$$
* **Strategic Utility:** This weight acts as a defensive shield. The bot will gladly bypass a high-scoring merge if it carries a risk of trapping tiles, prioritizing keeping the board "breathable" (maintaining empty spaces and open directions) to survive tight scenarios.

### 3. Neural Network Weights (The "Experience" Fine-Tuner)
While hand-crafted heuristics are excellent, they cannot easily capture subtle patterns—such as the exact distribution of other tiles on the board. The **Neural Network** ($16$ inputs $\rightarrow$ $16$ hidden neurons $\rightarrow$ $1$ output) learns these complex, non-linear board relationships over time.

* **Temporal Difference (TD) Learning:** As the bot trains, it evaluates board state $S$, plays a move to get a reward $R$ (normalized score gain) and next state $S'$. It calculates the target value:
  $$\text{Target} = Reward + \gamma \cdot Value(S')$$
* **Strategic Utility:** The network learns which board positions *actually* lead to high scores and long-term survival, adjusting the **synaptic weights** ($w_1, w_2$) via backpropagation. This learned score fine-tunes the heuristics, acting like a grandmaster's "intuition" to choose the path with the highest long-term probability of victory.

---

## Standalone Reversi (Othello) Game (`reversi.py`)

In addition to 2048, a fully featured **Reversi (Othello)** game is available as a standalone executable (`reversi.py`).

### Key Features
* **Double-Buffered Framebuffer Graphics (`-g` / `--graph`):** Renders a classic checkered wooden "Go-board" (with Burlywood and Warm Sienna alternating patterns and elegant dark borders) populated by **shiny, 3D-shaded obsidian (Black) and ivory (White) spherical discs** utilizing top-left specular highlights and radial diffuse shadows. It automatically detects display boundaries (adapting layouts dynamically to `240x240` or `320x320`).
* **Interactive Local Terminal Fallback:** Renders a gorgeous, high-contrast, fully playable 8x8 text matrix of `.`, `X`, and `O` on standard console windows using Rich.
* **Tactile Cursor Snapping:** Cursor automatically snaps to valid legal moves, and pressing Arrow keys or WASD hops the selector cursor exclusively between valid coordinates to ensure rapid, error-free play!
* **George Frideric Händel Victory Audio:** If an active ALSA driver is detected, plays Händel's famous victory chorus *"See, the conqu'ring hero comes!"* in raw 8-bit U8 PCM in the background.
* **Persistent Leaderboard:** Stores up to 20 high scores in `reversi_high_scores.json` detailing player name, friendly disc count, bot disc count, and timestamp.

### Master-Level AI Bot Heuristics
The Othello AI uses a depth-3/4 Minimax Search with Alpha-Beta Pruning, guided by a multi-phase evaluation function implementing expert game-theory:
1. **Positional Matrix weights:** Scores cells based on strategic values—corners are highly rewarded (`+100`), edges valued (`+10`), and dangerous X/C-squares heavily penalized (`-30` / `-15`).
2. **Dynamic Corner Locking:** C-squares and X-squares penalties are only active if their adjacent corner is empty. If the bot locks a corner, it safely utilizes adjacent squares as non-flippable anchors.
3. **Mobility Minimization:** Calculates legal move outcomes, aggressively picking paths that restrict the number of moves available to the opponent (forcing them into disadvantageous positions).
4. **Delayed Maximization (Phased Evaluation):**
   * **Opening & Midgame (< 50 discs):** Heavily penalizes taking too many friendly discs (focusing entirely on quiet moves, board position, and mobility).
   * **Endgame (>= 50 discs):** Shifts completely to maximizing final disc captures to secure victory.

### How to Run Reversi

* **To play on standard console terminal**:
  ```bash
  python3 reversi.py
  ```
* **To play with raw framebuffer graphics on Calculinux**:
  ```bash
  python3 reversi.py -g
  ```
