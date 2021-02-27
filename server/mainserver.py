from twisted.internet.protocol import Factory

from server import protocol
from networking import packet
from networking.utils import *


class ChessServer(Factory):
    def __init__(self):
        # all protocols connected to server
        self.connected_protocols: Dict[int, protocol.ChessProtocol] = {}
        for i in range(32):
            self.connected_protocols[i] = None

        self.number_of_connections = 0

        self.board = Map(8, 8, " ")     # 8x8 size
        self.build_board()

        self.turn = "W"

        self.white: Optional[protocol.ChessProtocol] = None
        self.black: Optional[protocol.ChessProtocol] = None
        # spectators are those is connected_protocols - [white, black]

    def buildProtocol(self, addr):
        proto = protocol.ChessProtocol(self)
        return proto

    def build_board(self):
        for x in range(0, 8):
            # white side
            self.board[0, x] = r10_to_r32(x)         # first row is [0, 7]
            self.board[1, x] = r10_to_r32(8 + x)     # pawns are [8, 15]

            # white pieces are < 16; else black

            # black side
            self.board[7, x] = r10_to_r32(16 + x)    # first row is [16, 23]
            self.board[6, x] = r10_to_r32(24 + x)    # pawns are [24, 31]

    def board_state_to_str(self):
        b = ""
        for row in range(0, 8):
            for col in range(0, 8):
                ch = self.board[row, col]
                if ch:
                    b += ch
                else:
                    b += " "

    def get_spectators(self):
        specs = set()

        for key, val in self.connected_protocols.items():
            if val is not None:
                if val != self.white and val != self.black:
                    specs.add(val)

        return specs
