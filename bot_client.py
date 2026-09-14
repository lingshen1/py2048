#!/usr/bin/env python3
import datetime
import json
import math
import os
import random
import socket
import sys
import time

WEIGHTS_FILE = "bot_weights.json"


class BoardValueNetwork:
    """A pure-Python feedforward Neural Network to approximate the board state value."""

    def __init__(self, input_dim=16, hidden_dim=16):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        
        # Xavier/He normal weight initialization
        self.w1 = [[random.normalvariate(0, math.sqrt(2.0 / input_dim)) for _ in range(hidden_dim)] for _ in range(input_dim)]
        self.b1 = [0.0] * hidden_dim
        
        self.w2 = [random.normalvariate(0, math.sqrt(2.0 / hidden_dim)) for _ in range(hidden_dim)]
        self.b2 = 0.0
        
        self.lr = 0.02  # Learning rate
        self.gamma = 0.90  # Discount factor for TD Learning
        
    def relu(self, x):
        return max(0.0, x)
        
    def relu_derivative(self, x):
        return 1.0 if x > 0.0 else 0.0
        
    def forward(self, x):
        # Hidden layer
        self.z1 = []
        self.a1 = []
        for j in range(self.hidden_dim):
            val = sum(x[i] * self.w1[i][j] for i in range(self.input_dim)) + self.b1[j]
            self.z1.append(val)
            self.a1.append(self.relu(val))
            
        # Output layer
        self.z2 = sum(self.a1[j] * self.w2[j] for j in range(self.hidden_dim)) + self.b2
        return self.z2
        
    def backward(self, x, target):
        # TD Target error gradient
        diff = self.z2 - target
        
        # Output layer gradients
        dw2 = [diff * self.a1[j] for j in range(self.hidden_dim)]
        db2 = diff
        
        # Hidden layer backprop error
        dz1 = [diff * self.w2[j] * self.relu_derivative(self.z1[j]) for j in range(self.hidden_dim)]
        
        # Hidden layer weights gradients
        dw1 = [[0.0] * self.hidden_dim for _ in range(self.input_dim)]
        for i in range(self.input_dim):
            for j in range(self.hidden_dim):
                dw1[i][j] = dz1[j] * x[i]
        db1 = dz1
        
        # Stochastic Gradient Descent updates
        for j in range(self.hidden_dim):
            self.w2[j] -= self.lr * dw2[j]
        self.b2 -= self.lr * db2
        
        for i in range(self.input_dim):
            for j in range(self.hidden_dim):
                self.w1[i][j] -= self.lr * dw1[i][j]
                self.b1[j] -= self.lr * db1[j]

    def save_weights(self, file_path=WEIGHTS_FILE):
        try:
            data = {
                "w1": self.w1,
                "b1": self.b1,
                "w2": self.w2,
                "b2": self.b2
            }
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving weights: {e}")

    def load_weights(self, file_path=WEIGHTS_FILE):
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    self.w1 = data["w1"]
                    self.b1 = data["b1"]
                    self.w2 = data["w2"]
                    self.b2 = data["b2"]
                print(f"Loaded trained neural network weights from {file_path}")
                return True
            except Exception as e:
                print(f"Failed to load weights from {file_path}: {e}")
        return False


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


def get_grid_features(grid):
    # Log2 scaling of tiles, normalized to [0, 1] as NN inputs
    features = []
    for r in range(4):
        for c in range(4):
            val = grid[r][c]
            features.append(0.0 if val == 0 else math.log2(val) / 16.0)
    return features


def evaluate_grid_hybrid(grid, net):
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
                
    heuristic_score = monotonicity_score
    
    if max_r == 3 and max_c == 3:
        heuristic_score += (4 ** 16) * math.log2(max_tile)
    else:
        heuristic_score -= (4 ** 17) * math.log2(max_tile)
        
    bottom_row_full = all(grid[3][c] != 0 for c in range(4))
    if bottom_row_full:
        heuristic_score += 4 ** 14
    else:
        empty_bottom = sum(1 for c in range(4) if grid[3][c] == 0)
        heuristic_score -= (4 ** 14) * empty_bottom
        
    smoothness = 0
    for r in range(4):
        for c in range(4):
            if grid[r][c] != 0:
                if c < 3 and grid[r][c] == grid[r][c+1]:
                    smoothness += math.log2(grid[r][c]) * (4 ** W_MATRIX[r][c])
                if r < 3 and grid[r][c] == grid[r+1][c]:
                    smoothness += math.log2(grid[r][c]) * (4 ** W_MATRIX[r][c])
    heuristic_score += smoothness
    heuristic_score += empty_cells * (4 ** 9)
    
    # 2. Add Neural Network state value approximation
    features = get_grid_features(grid)
    nn_val = net.forward(features) * (4 ** 12)  # Scale NN output to align with heuristics
    
    return heuristic_score + nn_val


def expectimax_client(grid, depth, is_player, net):
    empty_cells = [(r, c) for r in range(4) for c in range(4) if grid[r][c] == 0]
    
    valid_moves = []
    for d in ["s", "d", "a", "w"]:
        _, changed, _ = simulate_move(grid, d)
        if changed:
            valid_moves.append(d)
            
    if is_player and not valid_moves:
        return -10**18 + (depth * 10**12)
        
    if depth == 0:
        return evaluate_grid_hybrid(grid, net)
        
    if is_player:
        best_score = -float('inf')
        for d in valid_moves:
            next_grid, _, _ = simulate_move(grid, d)
            score = expectimax_client(next_grid, depth - 1, False, net)
            if d in ["a", "w"]:
                score -= (4 ** 14)
            best_score = max(best_score, score)
        return best_score
    else:
        if not empty_cells:
            return evaluate_grid_hybrid(grid, net)
            
        total_score = 0
        for r, c in empty_cells:
            grid[r][c] = 2
            score_2 = expectimax_client(grid, depth - 1, True, net)
            grid[r][c] = 4
            score_4 = expectimax_client(grid, depth - 1, True, net)
            grid[r][c] = 0
            total_score += 0.9 * score_2 + 0.1 * score_4
            
        return total_score / len(empty_cells)


def send_to_server(sock, server_addr, command):
    try:
        sock.sendto(command.encode("utf-8"), server_addr)
        sock.settimeout(2.0)
        data, _ = sock.recvfrom(4096)
        return json.loads(data.decode("utf-8"))
    except socket.timeout:
        print("[red]Connection timeout. Is 2048 UDP server running?[/red]")
        return None
    except Exception as e:
        print(f"Network error: {e}")
        return None


def play_game(sock, server_addr, net, train_mode=False):
    # Get initial state
    state = send_to_server(sock, server_addr, "state")
    if not state:
        print("Failed to initialize game state from server. Exiting.")
        return 0, 0
        
    game_score = 0
    recalls = 0
    move_count = 0
    
    while True:
        grid = state["grid"]
        game_score = state["score"]
        game_over = state["game_over"]
        
        if game_over:
            # End of game, trigger restart if in training mode
            break
            
        empty_count = sum(1 for r in range(4) for c in range(4) if grid[r][c] == 0)
        depth = 4 if empty_count < 5 else (3 if empty_count < 9 else 2)
        
        best_move = None
        best_score = -float('inf')
        
        for d in ["s", "d", "a", "w"]:
            next_grid, changed, _ = simulate_move(grid, d)
            if changed:
                score = expectimax_client(next_grid, depth - 1, False, net)
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
                    
        if best_move is None:
            break
            
        # Capture pre-move features
        features_S = get_grid_features(grid)
        
        # Send action to server
        new_state = send_to_server(sock, server_addr, best_move)
        if not new_state:
            break
            
        reward = (new_state["score"] - game_score) / 100.0  # Normalize reward
        
        if train_mode:
            # TD Target calculation: Target = reward + gamma * Value(S')
            features_S_prime = get_grid_features(new_state["grid"])
            v_s_prime = net.forward(features_S_prime)
            
            if new_state["game_over"]:
                # terminal state
                target = reward
            else:
                target = reward + net.gamma * v_s_prime
                
            # Perform backpropagation update
            net.forward(features_S)  # Repopulate activations for backprop
            net.backward(features_S, target)
            
        state = new_state
        move_count += 1
        
        if not train_mode:
            # Show progress in console
            print(f"Move {move_count}: {best_move.upper()} | Score: {state['score']}", end="\r")
            time.sleep(0.05)  # slight sleep for visual display during play mode
            
    if not train_mode:
        print()
    return game_score, move_count


def show_help():
    print("""
2048 Trainable Neural Network Bot Client

Usage:
  python3 bot_client.py [options]

Options:
  -s, --server <ip:port>   Specify server address (default: 127.0.0.1:10000)
  -p, --play               Connect and play 1 interactive live game
  -t, --train <games>      Play specified number of games in Fast Training Mode
  -h, --help               Show this help text
""")


def main():
    server_ip = "127.0.0.1"
    server_port = 10000
    mode = "play"
    train_games = 10
    
    # Simple CLI parsing
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ["-s", "--server"]:
            if i + 1 < len(args):
                parts = args[i+1].split(":")
                server_ip = parts[0]
                if len(parts) > 1:
                    server_port = int(parts[1])
                i += 2
                continue
        elif arg in ["-p", "--play"]:
            mode = "play"
            i += 1
            continue
        elif arg in ["-t", "--train"]:
            mode = "train"
            if i + 1 < len(args):
                try:
                    train_games = int(args[i+1])
                    i += 2
                    continue
                except ValueError:
                    pass
            i += 1
            continue
        elif arg in ["-h", "--help"]:
            show_help()
            return
        else:
            print(f"Unknown argument: {arg}")
            show_help()
            return
            
    server_addr = (server_ip, server_port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    net = BoardValueNetwork()
    net.load_weights()
    
    if mode == "play":
        print(f"Starting 1 live game on server {server_ip}:{server_port}...")
        score, moves = play_game(sock, server_addr, net, train_mode=False)
        print(f"Game finished! Final Score: {score} | Total Moves: {moves}")
    elif mode == "train":
        print(f"Launching Fast Training Mode for {train_games} games...")
        scores_history = []
        for g in range(train_games):
            print(f"Game {g+1}/{train_games} starting...", end="")
            sys.stdout.flush()
            
            # Send a trigger to reset/restart server to start a clean game!
            reset_state = send_to_server(sock, server_addr, "reset")
            if not reset_state:
                print("\nError: Failed to reset server board state. Is server active?")
                break
                
            score, moves = play_game(sock, server_addr, net, train_mode=True)
            scores_history.append(score)
            print(f" Completed! Score: {score} | Moves: {moves}")
            
        if scores_history:
            avg_score = sum(scores_history) / len(scores_history)
            max_score = max(scores_history)
            print(f"\n--- Training completed! ---")
            print(f"Games Played: {len(scores_history)}")
            print(f"Average Score: {avg_score:.1f}")
            print(f"Highest Score: {max_score}")
            net.save_weights()
            print(f"Saved optimized neural network weights to {WEIGHTS_FILE}")


if __name__ == "__main__":
    main()