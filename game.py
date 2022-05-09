'''
handles the game logic and producing the logs
'''
from ast import Assert
from enum import Enum
import numpy as np
import io


class Turn(Enum):
    WHITE = 1
    BLACK = 2

class Piece(Enum):
    E = 0
    WK = 1
    WQ = 2
    WR = 3
    WB = 4
    WN = 5
    WP = 6
    BK = 7
    BQ = 8
    BR = 9
    BB = 10
    BN = 11
    BP = 12
    
piece_chars = {
    Piece.WK: 'K',
    Piece.WQ: 'Q',
    Piece.WR: 'R',
    Piece.WB: 'B',
    Piece.WN: 'N',
    Piece.WP: 'P',
    Piece.BK: 'k',
    Piece.BQ: 'q',
    Piece.BB: 'b',
    Piece.BR: 'r',
    Piece.BN: 'n',
    Piece.BP: 'p'
}

class Board:
    def __init__(self) -> None:
        self.board =  np.array([[Piece.BR, Piece.BN, Piece.BB, Piece.BQ, Piece.BK, Piece.BB, Piece.BN, Piece.BR],
                                [Piece.BP, Piece.BP, Piece.BP, Piece.BP, Piece.BP, Piece.BP, Piece.BP, Piece.BP],
                                [Piece.E, Piece.E, Piece.E, Piece.E, Piece.E, Piece.E, Piece.E, Piece.E],
                                [Piece.E, Piece.E, Piece.E, Piece.E, Piece.E, Piece.E, Piece.E, Piece.E],
                                [Piece.E, Piece.E, Piece.E, Piece.E, Piece.E, Piece.E, Piece.E, Piece.E],
                                [Piece.E, Piece.E, Piece.E, Piece.E, Piece.E, Piece.E, Piece.E, Piece.E],
                                [Piece.WP, Piece.WP, Piece.WP, Piece.WP, Piece.WP, Piece.WP, Piece.WP, Piece.WP],
                                [Piece.WR, Piece.WN, Piece.WB, Piece.WQ, Piece.WK, Piece.WB, Piece.WN, Piece.WR]],
                                dtype=Piece)
        self.filled_board = np.array([[2, 2, 2, 2, 2, 2, 2, 2],
                                      [2, 2, 2, 2, 2, 2, 2, 2],
                                      [0, 0, 0, 0, 0, 0, 0, 0],
                                      [0, 0, 0, 0, 0, 0, 0, 0],
                                      [0, 0, 0, 0, 0, 0, 0, 0],
                                      [0, 0, 0, 0, 0, 0, 0, 0],
                                      [1, 1, 1, 1, 1, 1, 1, 1],
                                      [1, 1, 1, 1, 1, 1, 1, 1]])
        self.turn = Turn.WHITE
        self.verify_board()

    def get_fen_for_new_state(self, input_board):
        self.calculate_difference(input_board)
        self.verify_board()
        return self.board_to_fen()

    def calculate_difference(self, input_filled_or_not):
        has_piece_been_taken = np.sum(self.filled_board) - np.sum(input_filled_or_not)
        if has_piece_been_taken==0:
            # no piece taken
            differences = input_filled_or_not - self.filled_board
            for i in range(8):
                for j in range(8):
                    # If the old square was empty but now was filled, differences is 1 or 2
                    if differences[i][j] == 1 or differences[i][j] == 2:
                        x_new = i
                        y_new = j
                    if differences[i][j] < 0:
                        # If the old square was filled but now is empty, difference is -1 or -2
                        x_old = i
                        y_old = j
        else:
            # piece taken
            find_taken_piece_board = input_filled_or_not + self.filled_board
            differences = input_filled_or_not - self.filled_board
            for i in range(8):
                for j in range(8):
                    # only if it used to be a piece, and then it's a different color piece, so we have 1 + 2 = 3
                    if find_taken_piece_board[i][j] == 3:
                        x_new = i
                        y_new = j
                    if differences[i][j] < 0:
                        # If the old square was filled but now is empty, difference is -1 or -2
                        x_old = i
                        y_old = j
        # Run updates
        self.update_after_turn(input_filled_or_not, x_new, y_new, x_old, y_old)

# WQ 2, 2
# BR 3, 3
# old filled board at 2,2 is 1 (WHITE)
# at 3,3 is 2 (black)
# new input at 2,2 is 0
# new input at 3,3 is 1

    def update_pieces(self, x_new, y_new, x_old, y_old):
        self.board[x_new, y_new] = self.board[x_old, y_old]
        self.board[x_old, y_old] = Piece.E

    def update_after_turn(self, new_filled_board, x_new, y_new, x_old, y_old):
        self.filled_board = new_filled_board
        self.update_pieces(x_new, y_new, x_old, y_old)
        if self.turn==Turn.WHITE:
            self.turn = Turn.BLACK
        else:
            self.turn = Turn.WHITE

    def print_board(self):
        print(self.board)

    def verify_board(self):
        for i in range(8):
            for j in range(8):
                current_piece = self.board[i][j]
                if current_piece==Piece.E:
                    Assert(self.filled_board[i][j]==0)
                elif current_piece==Piece.WK or current_piece==Piece.WQ or current_piece==Piece.WR or current_piece==Piece.WB or current_piece==Piece.WN or current_piece==Piece.WP:
                    Assert(self.filled_board[i][j]==1)
                elif current_piece==Piece.BK or current_piece==Piece.BQ or current_piece==Piece.BR or current_piece==Piece.BB or current_piece==Piece.BN or current_piece==Piece.BP:
                    Assert(self.filled_board[i][j]==2)
        print("Board seems good!")
        self.print_board()

# https://stackoverflow.com/questions/56754543/generate-chess-board-diagram-from-an-array-of-positions-in-python

    def board_to_fen(self):
        # Use StringIO to build string more efficiently than concatenating
        with io.StringIO() as s:
            for row in self.board:
                empty = 0
                for cell in row:
                    c = int(cell)
                    if not c==0:
                        if empty > 0:
                            s.write(str(empty))
                            empty = 0
                        s.write(piece_chars[cell])
                    else:
                        empty += 1
                if empty > 0:
                    s.write(str(empty))
                s.write('/')
            # Move one position back to overwrite last '/'
            s.seek(s.tell() - 1)
            # If you do not have the additional information choose what to put
            s.write(' w KQkq - 0 1')
            return s.getvalue()
