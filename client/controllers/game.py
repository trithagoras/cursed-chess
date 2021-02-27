import curses
import curses.ascii

from client.controllers.controller import Controller
from client.controllers.widgets import TextField
from client.views.gameview import GameView
from networking.logger import Log
from networking.utils import *
from networking import packet


class Participant:
    def __init__(self, id: int, username: str, role: str):
        self.id = id
        self.username = username
        self.role = role


class Game(Controller):
    def __init__(self, cs):
        super().__init__(cs)
        self.cursor_y = 0
        self.cursor_x = 0
        self.selected = None

        self.player = None

        self.board = Map(8, 8, ' ')

        self.participants: Dict[int, Optional[Participant]] = {}
        for i in range(32):
            self.participants[i] = None

        self.white: Optional[Participant] = None
        self.black: Optional[Participant] = None

        self.turn = "W"

        self.logger = Log()
        self.chatbox = TextField(self, title="Say: ", max_length=80)

        self.view = GameView(self)

    def count_spectators(self):
        count = 0

        for key, val in self.participants.items():
            if val:
                count += 1

        if self.white:
            count -= 1
        if self.black:
            count -= 1

        return count

    def ready(self):
        return None not in [self.player]

    def process_packet(self, p) -> bool:
        pid = r32_to_r10(p[0])

        if pid == packet.BOARD_STATE:
            s = p[1:]
            self.board = Map.string_to_board(s)
        elif pid == packet.ID:
            self.player = self.participants[r32_to_r10(p[1])]
        elif pid == packet.PERSON:
            id = r32_to_r10(p[1])
            role = p[2]
            name = p[3:]
            part = Participant(id, name, role)
            self.participants[id] = part
            if role == 'W':
                self.white = part
            elif role == 'B':
                self.black = part
        elif pid == packet.GOODBYE:
            id = r32_to_r10(p[1])
            part = self.participants[id]

            # if a player
            if part == self.white:
                self.white = None
            elif part == self.black:
                self.black = None
            self.participants[id] = None
        elif pid == packet.WHOSETURN:
            self.turn = p[1]
        elif pid == packet.MOVE:
            self.move(p)
        elif pid == packet.LOG:
            self.logger.log(p[1:])
        else:
            return False

        return True

    def process_input(self, key: int) -> bool:
        if key == curses.KEY_UP:
            self.cursor_y -= 1
            if self.cursor_y == -1:
                self.cursor_y = 7
        elif key == curses.KEY_DOWN:
            self.cursor_y += 1
            if self.cursor_y == 8:
                self.cursor_y = 0
        elif key == curses.KEY_LEFT:
            self.cursor_x -= 1
            if self.cursor_x == -1:
                self.cursor_x = 7
        elif key == curses.KEY_RIGHT:
            self.cursor_x += 1
            if self.cursor_x == 8:
                self.cursor_x = 0
        elif key == curses.ascii.ESC:
            self.process_exit()
        elif key == ord("\n"):
            self.select_here()
        if self.chatbox.selected:
            if key == ord('\n'):
                self.cs.ns.send_packet(packet.construct_chat_packet(self.chatbox.value))
                self.chatbox.value = ""
                self.chatbox.cursor = 0
            self.chatbox.process_input(key)
            return True
        elif key == ord('t'):
            self.chatbox.select()
        else:
            return False
        return True

    def select_here(self):
        if self.player != self.white and self.player != self.black:
            return

        # is it your turn?
        if self.player == self.white:
            if self.turn == 'B':
                return
        else:
            if self.turn == 'W':
                return

        piece = self.board[self.cursor_y, self.cursor_x]

        if self.selected == piece:
            self.selected = None
            return

        if self.selected:
            if (self.cursor_y, self.cursor_x) in self.board.moveable_positions(self.selected):
                # move piece to this spot
                self.cs.ns.send_packet(packet.construct_move_packet(r32_to_r10(self.selected), self.cursor_y, self.cursor_x))
                self.selected = None

        if piece == ' ':
            self.selected = None
            return

        dec = r32_to_r10(piece)

        if self.player == self.white:
            if dec < 16:
                return
            self.selected = piece
        else:
            if dec >= 16:
                return
            self.selected = piece

        # at this point, a piece is selected

    def move(self, p: str):
        piece = p[1]
        y = r32_to_r10(p[2])
        x = r32_to_r10(p[3])

        if (y, x) in self.board.moveable_positions(piece):
            # good
            self.board.move(piece, y, x)

    def process_exit(self):
        self.cs.ns.disconnect()
        self.cs.change_controller("MainMenu")
