import curses
import time

from client.views.view import View, Window
from networking.utils import *


def get_char_from_id(id: int) -> str:
    if id in KNIGHTS:
        return "k"
    elif id in BISHOPS:
        return "b"
    elif id in QUEENS:
        return "Q"
    elif id in KINGS:
        return "K"
    elif id in ROOKS:
        return "r"
    elif id in PAWNS:
        return "p"


class GameView(View):
    def __init__(self, controller):
        super().__init__(controller)

        self.visible_log: Dict[float, str] = {}
        self.times_logged: int = 0

        self.win3 = Window(self.controller.cs.stdscr, 21, 0, 13, 80)
        self.chatwin = Window(self.controller.cs.stdscr, self.win3.y + self.win3.height - 1, self.win3.x, 3,
                              self.win3.width)
        self.place_widget(self.controller.chatbox, self.chatwin.y + 1, self.chatwin.x + 2)

    def draw(self):
        if not self.controller.ready():
            msg: str = "Loading, please wait..."
            self.addstr(35 // 2, (80 - len(msg)) // 2, msg)
            return

        self.draw_log()

        # draw grid lines
        self.addstr(2, 4, "+ - + - + - + - + - + - + - + - +", 10)
        for y in range(1, 16, 2):
            self.addstr(2 + y, 4, "|   |   |   |   |   |   |   |   |", 10)

        for y in range(2, 15, 2):
            self.addstr(2 + y, 4, "| - + - + - + - + - + - + - + - |", 10)

        self.addstr(18, 4, "+ - + - + - + - + - + - + - + - +", 10)

        self.draw_board_state()

        # cursor
        self.addstr(3 + self.controller.cursor_y * 2, 6 + self.controller.cursor_x * 4, "X")

        # black player
        self.addstr(2, 40, self.controller.black.username if self.controller.black else "")

        # white player
        self.addstr(18, 40, self.controller.white.username if self.controller.white else "")

        # spectators
        self.addstr(20, 40, f"Spectators: {self.controller.count_spectators()}/30")

        # me
        self.addstr(1, 4, self.controller.player.username)

        # whose turn it is
        if self.controller.turn == 'W':
            self.addstr(18, 39, "*", curses.COLOR_GREEN)
        else:
            self.addstr(2, 39, "*", curses.COLOR_GREEN)

        # selected piece
        self.addstr(22, 40, self.controller.selected)

    def draw_board_state(self):
        for row in range(0, 8):
            for col in range(0, 8):
                ch = self.controller.board[row, col]

                y = 3 + row * 2
                x = 6 + col * 4

                if ch == ' ':
                    if self.controller.selected is not None:
                        if (row, col) in self.controller.board.moveable_positions(self.controller.selected):
                            self.addstr(y, x, " ", curses.COLOR_WHITE)
                    continue

                dec_id = r32_to_r10(ch)
                if dec_id < 16:
                    # black
                    col = curses.COLOR_YELLOW
                else:
                    # white
                    col = curses.COLOR_CYAN

                if self.controller.selected == ch:
                    col = curses.COLOR_MAGENTA
                self.addstr(y, x, get_char_from_id(dec_id), col)

    def draw_log(self):
        # self.win3.border()
        self.win3.title("Log")

        # Update the log if necessary
        logsize_diff: int = self.controller.logger.size - self.times_logged
        if logsize_diff > 0:
            self.visible_log.update(self.controller.logger.latest)
            self.times_logged += logsize_diff

            # Truncate the log to only the newest entries that will fit in the view
            log_keys = list(self.visible_log.keys())
            log_keys_to_remove = log_keys[:max(0, len(log_keys) - self.win3.height + self.chatwin.height)]
            for key in log_keys_to_remove:
                del self.visible_log[key]

        if self.visible_log != {}:
            log_line: int = 2
            for utctime, message in self.visible_log.items():
                timestamp: str = time.strftime('%R', time.localtime(utctime))
                self.win3.addstr(log_line, 1, f" [{timestamp}] {message}")
                log_line += 1

        # Add chat prompt
        self.controller.chatbox.draw()