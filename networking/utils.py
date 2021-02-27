from typing import *


R32 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"


def r10_to_r32(num: int):
    if 0 <= num <= 31:
        return R32[num]
    raise Exception("Number out of range")


def r32_to_r10(ch: str):
    if len(ch) == 1 and ch in R32:
        num = R32.find(ch)
        return num
    raise Exception("string needs length 1 and in R32")


def is_white(ch: str):
    return r32_to_r10(ch) >= 16


# what each piece id corresponds to class-wise. e.g. piece with id=15 is a pawn (specifically the rightmost white pawn)
ROOKS = [0, 7, 16, 23]
KNIGHTS = [1, 6, 17, 22]
BISHOPS = [2, 5, 18, 21]
QUEENS = [3, 19]
KINGS = [4, 20]
PAWNS = list(range(8, 16)) + list(range(24, 32))


class Map:
    def __init__(self, height, width, default_value=0):
        self.height = height
        self.width = width

        self.internal: Dict[Tuple[int, int], Any] = {}
        for row in range(0, height):
            for col in range(0, width):
                self.internal[(row, col)] = default_value

        self.white_check = False
        self.black_check = False

    def __getitem__(self, item: Tuple[int, int]):
        return self.internal[item]

    def __setitem__(self, key: Tuple[int, int], value: Any):
        self.internal[key] = value

    def find_position(self, piece: str) -> Tuple[int, int]:
        for key, val in self.internal.items():
            if val == piece:
                return key

    def board_to_string(self) -> str:
        """Gives a single line representation of the board using ids. ' ' = empty"""

        s = ""

        for row in range(0, self.height):
            for col in range(0, self.width):
                s += self[row, col]

        return s

    @staticmethod
    def string_to_board(s: str) -> 'Map':
        """Takes a single line representation of the board and builds a Map from it"""

        board = Map(8, 8)
        for i in range(64):
            row = i // 8
            col = i % 8
            board[row, col] = s[i]

        return board

    def moveable_positions(self, piece: str) -> List[Tuple[int, int]]:
        white = True

        dec = r32_to_r10(piece)

        if dec < 16:
            white = False

        y, x = self.find_position(piece)

        moveable_positions = []
        if white:
            if dec in PAWNS:
                if y == 6:
                    moveable_positions.append((y - 2, x))
                moveable_positions.append((y - 1, x))

        else:
            if dec in PAWNS:
                if y == 1:
                    moveable_positions.append((y + 2, x))
                moveable_positions.append((y + 1, x))

        # remove positions where a friendly piece is on
        for (y, x) in moveable_positions:
            here = self[y, x]
            if here != " " and is_white(here) == white:
                moveable_positions.remove((y, x))

        return moveable_positions

    def move(self, piece: str, y: int, x: int):
        old_y, old_x = self.find_position(piece)

        self[old_y, old_x] = ' '

        # kills piece that was here
        self.kill(self[y, x])

        self[y, x] = piece

    def kill(self, piece):
        pass
