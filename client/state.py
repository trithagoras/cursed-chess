import curses
import socket
import threading
import time

from client.controllers import menus
from client.controllers.game import Game
from client.controllers.menus import UsernameMenu
from client.views.view import Window


class NetworkState:
    """
    Higher level abstraction for keeping network state. Keeps public_key and socket in neat spot.
    """

    def __init__(self):
        self.socket = None
        self.clientid = 0
        self.connected = False

    def connect(self, host: str, port: int) -> bool:
        address = (host, port)

        try:
            s = socket.create_connection(address)

            self.socket = s
            self.connected = True
            return True

        except Exception:
            return False

    def disconnect(self):
        if not self.connected:
            return

        self.socket.close()
        self.socket = None
        self.connected = False

    def send_packet(self, p: str):
        """
        Converts packet to bytes; then encrypts bytes; then converts to netstring; then send over socket
        :param p: packet to send
        """

        self._send(p, self.socket)

    def receive_packet(self) -> str:
        return self._receive(self.socket)

    def _to_netstring(self, data: bytes) -> bytes:
        length = len(data)
        return str(length).encode('ascii') + b':' + data + b','

    def _send(self, p: str, s) -> bytes:
        """
        Converts a Packet to bytes and sends it over a socket. Ensures all the data is sent and no more.
        """

        b = self._to_netstring(p.encode('ascii'))

        failure = s.sendall(b)
        if failure is not None:
            self._send(p, s)
        return b

    def _receive(self, s) -> str:
        length: bytes = b''
        while len(length) <= 2048:
            c: bytes = s.recv(1)
            if c != b':':
                try:
                    int(c)
                except ValueError:
                    raise PacketParseError(
                        f"Error reading packet length. So far got {length} but next digit came in as {c}.")
                else:
                    length += c
            else:
                if len(length) < 1:
                    raise PacketParseError(f"Parsing packet but length doesn't seem to be a number. Got {length}.")
                data: bytes = s.recv(int(length))

                # Perhaps all the data is not received yet
                while len(data) < int(length):
                    nextLength = int(length) - len(data)
                    data += s.recv(nextLength)

                # Read off the trailing comma
                s.recv(1)
                return data.decode('ascii')

        raise PacketParseError("Error reading packet length. Too long.")


class PacketParseError(Exception):
    pass


class ClientState:
    def __init__(self, stdscr):
        self.ns = NetworkState()
        self.controller = None
        self.stdscr = stdscr
        self.running = True

        self.window = Window(self.stdscr, 0, 0, 40, 80)

        self.packets = []

        # Listen for data in its own thread
        threading.Thread(target=self._receive_data, daemon=True).start()

        self.init_curses()
        self.change_controller("MainMenu")

    def init_curses(self):
        self.stdscr.keypad(True)
        self.stdscr.nodelay(True)

        # Start colors in curses
        curses.start_color()

        # Init color pairs
        curses.init_pair(curses.COLOR_WHITE, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(curses.COLOR_CYAN, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(curses.COLOR_RED, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(curses.COLOR_GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(curses.COLOR_MAGENTA, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(curses.COLOR_YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(curses.COLOR_BLUE, curses.COLOR_BLUE, curses.COLOR_BLACK)

        # dark gray
        curses.init_color(10, 200, 200, 200)
        curses.init_pair(10, 10, curses.COLOR_BLACK)

        curses.curs_set(False)

    def change_controller(self, controller: str):
        if self.controller:
            self.controller.stop()
        if controller == Game.__name__:
            self.controller = Game(self)
        elif controller == menus.UsernameMenu.__name__:
            self.controller = UsernameMenu(self)
        elif controller == menus.MainMenu.__name__:
            self.controller = menus.MainMenu(self)

        self.controller.start()

    def _receive_data(self):
        while self.running:
            if self.ns.connected:
                try:
                    p = self.ns.receive_packet()
                    self.packets.append(p)
                except Exception as e:
                    pass
            time.sleep(0.2)
