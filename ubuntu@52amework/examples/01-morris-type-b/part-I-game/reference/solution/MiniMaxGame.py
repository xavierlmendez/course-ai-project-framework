import sys

# ---------------------------------------------------------------------------
# Board representation: 23-char string, indices 0-22
# Pieces: 'W' = White, 'B' = Black, 'x' = empty
# ---------------------------------------------------------------------------

NEIGHBORS = {
    0:  [1, 3, 8],
    1:  [0, 2, 4],
    2:  [1, 5, 13],
    3:  [0, 4, 6, 9],
    4:  [1, 3, 5],
    5:  [2, 4, 7, 12],
    6:  [3, 10],
    7:  [5, 11],
    8:  [0, 9, 20],
    9:  [3, 8, 10, 17],
    10: [6, 9, 14],
    11: [7, 12, 16],
    12: [5, 11, 13, 19],
    13: [2, 12, 22],
    14: [10, 15, 17],
    15: [14, 16, 18],
    16: [11, 15, 19],
    17: [9, 14, 18, 20],
    18: [15, 17, 19, 21],
    19: [12, 16, 18, 22],
    20: [8, 17, 21],
    21: [20, 18, 22],
    22: [13, 19, 21],
}

MILLS = [
    (0, 1, 2), (3, 4, 5), (8, 9, 10), (11, 12, 13),
    (14, 15, 16), (17, 18, 19), (20, 21, 22),
    (0, 8, 20), (2, 13, 22),
    (3, 9, 17), (5, 12, 19),
    (6, 10, 14), (7, 11, 16),
    (0, 3, 6), (2, 5, 7), (14, 17, 20), (16, 19, 22),
    (15, 18, 21),
]


def close_mill(location, board):
    c = board[location]
    for mill in MILLS:
        if location in mill:
            if all(board[pos] == c for pos in mill if pos != location):
                return True
    return False


def swap_colors(board):
    result = []
    for ch in board:
        if ch == 'W':
            result.append('B')
        elif ch == 'B':
            result.append('W')
        else:
            result.append(ch)
    return ''.join(result)


def generate_remove(board, L):
    added = False
    for i in range(23):
        if board[i] == 'B' and not close_mill(i, board):
            L.append(board[:i] + 'x' + board[i+1:])
            added = True
    if not added:
        L.append(board)


def generate_add(board):
    L = []
    for i in range(23):
        if board[i] == 'x':
            b = board[:i] + 'W' + board[i+1:]
            if close_mill(i, b):
                generate_remove(b, L)
            else:
                L.append(b)
    return L


def generate_move(board):
    L = []
    for i in range(23):
        if board[i] == 'W':
            for j in NEIGHBORS[i]:
                if board[j] == 'x':
                    b = board[:i] + 'x' + board[i+1:]
                    b = b[:j] + 'W' + b[j+1:]
                    if close_mill(j, b):
                        generate_remove(b, L)
                    else:
                        L.append(b)
    return L


def generate_hopping(board):
    L = []
    for i in range(23):
        if board[i] == 'W':
            for j in range(23):
                if board[j] == 'x':
                    b = board[:i] + 'x' + board[i+1:]
                    b = b[:j] + 'W' + b[j+1:]
                    if close_mill(j, b):
                        generate_remove(b, L)
                    else:
                        L.append(b)
    return L


def generate_moves_opening(board):
    return generate_add(board)


def generate_moves_midgame_endgame(board):
    if board.count('W') == 3:
        return generate_hopping(board)
    return generate_move(board)


def generate_moves_opening_black(board):
    swapped = swap_colors(board)
    return [swap_colors(b) for b in generate_add(swapped)]


def generate_moves_midgame_endgame_black(board):
    swapped = swap_colors(board)
    return [swap_colors(b) for b in generate_moves_midgame_endgame(swapped)]


def static_estimation_midgame_endgame(board):
    num_white = board.count('W')
    num_black = board.count('B')
    num_black_moves = len(generate_moves_midgame_endgame(swap_colors(board)))
    if num_black <= 2:
        return 10000
    if num_white <= 2:
        return -10000
    if num_black_moves == 0:
        return 10000
    return 1000 * (num_white - num_black) - num_black_moves


# ---------------------------------------------------------------------------
# Minimax search
# ---------------------------------------------------------------------------

positions_evaluated = 0


def minimax_game(board, depth, is_max_player):
    global positions_evaluated
    if depth == 0:
        positions_evaluated += 1
        return static_estimation_midgame_endgame(board)

    if is_max_player:
        moves = generate_moves_midgame_endgame(board)
        if not moves:
            positions_evaluated += 1
            return static_estimation_midgame_endgame(board)
        best = -float('inf')
        for m in moves:
            val = minimax_game(m, depth - 1, False)
            if val > best:
                best = val
        return best
    else:
        moves = generate_moves_midgame_endgame_black(board)
        if not moves:
            positions_evaluated += 1
            return static_estimation_midgame_endgame(board)
        best = float('inf')
        for m in moves:
            val = minimax_game(m, depth - 1, True)
            if val < best:
                best = val
        return best


def best_game_move(board, depth):
    global positions_evaluated
    positions_evaluated = 0
    moves = generate_moves_midgame_endgame(board)
    best_board = None
    best_val = -float('inf')
    for m in moves:
        val = minimax_game(m, depth - 1, False)
        if val > best_val or best_board is None:
            best_val = val
            best_board = m
    return best_board, best_val


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) != 4:
        print("Usage: python3 MiniMaxGame.py <input> <output> <depth>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    depth = int(sys.argv[3])

    with open(input_file, 'r') as f:
        board = f.read().strip()

    best_board, estimate = best_game_move(board, depth)

    with open(output_file, 'w') as f:
        f.write(best_board + '\n')

    print(f"Board Position: {best_board}")
    print(f"Positions evaluated by static estimation: {positions_evaluated}.")
    print(f"MINIMAX estimate: {estimate}.")


if __name__ == '__main__':
    main()
