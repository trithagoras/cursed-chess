from twisted.internet.protocol import connectionDone
from twisted.protocols.basic import NetstringReceiver
from networking import packet
from networking.logger import Log
from networking.utils import *


class ChessProtocol(NetstringReceiver):
    def __init__(self, server):
        self.server = server
        self.state = self.ENTRY
        self.in_game = False
        self.id = 0
        self.username = ""

        self.logger = Log()

    def connectionMade(self):
        if self.server.number_of_connections >= 32:
            self.send_packet(packet.construct_no_packet("Server is full."))
            self.transport.loseConnection()
            print("A new client tried joining, but the server was full.")
            return

        self.server.number_of_connections += 1

        for key, val in self.server.connected_protocols.items():
            if val is None:
                self.server.connected_protocols[key] = self
                self.id = key
                break

        print("Added new client")

        self.send_packet(packet.construct_ok_packet())

    def connectionLost(self, reason=connectionDone):
        print("Connection lost")
        self.broadcast(packet.construct_goodbye_packet(self.id))

        # if a player
        if self == self.server.white:
            self.server.white = None
        elif self == self.server.black:
            self.server.black = None

        self.server.connected_protocols[self.id] = None
        self.server.number_of_connections -= 1

    def stringReceived(self, string):
        # packet structure: id (1 byte), payloads (depends on id)
        s = string.decode('ascii')
        print(s)
        self.handle_packet_from_client(s)

    def send_packet(self, p: str):
        s = p.encode('ascii')
        self.sendString(s)
        print(f"Sent packet to client @ {self.id}: {s}")

    def handle_packet_from_proto(self, p: str):
        self.state(p, from_client=False)

    def handle_packet_from_client(self, p: str):
        self.state(p)

    def broadcast(self, p: str, include_self=False):
        protos = set(self.server.connected_protocols.values())
        protos.remove(None)
        if not include_self:
            protos.remove(self)

        for proto in protos:
            proto.handle_packet_from_proto(p)

    def ENTRY(self, p: str, from_client=True):
        pid = r32_to_r10(p[0])

        if from_client:
            if pid == packet.USERNAME:
                username = p[1:]
                # check if player in room already has this username
                for proto in self.server.connected_protocols.values():
                    if not proto:
                        continue

                    if proto.in_game:
                        if username == proto.username:
                            self.send_packet(packet.construct_no_packet("Player in room already has this username."))
                            return
                self.send_packet(packet.construct_ok_packet())
                self.username = username

                self.enter_game()
        else:
            pass

    def enter_game(self):
        self.state = self.PLAY
        self.in_game = True

        self.send_packet(packet.construct_board_state_packet(self.server.board.board_to_string()))

        if not self.server.white:
            self.server.white = self
            self.broadcast(packet.construct_person_packet(self.id, 'W', self.username))
        else:
            if not self.server.black:
                self.server.black = self
                self.broadcast(packet.construct_person_packet(self.id, 'B', self.username))
            else:
                self.broadcast(packet.construct_person_packet(self.id, 'S', self.username))

        w = self.server.white
        b = self.server.black

        if w:
            self.send_packet(packet.construct_person_packet(w.id, 'W', self.server.white.username))     # white
        if b:
            self.send_packet(packet.construct_person_packet(b.id, 'B', self.server.black.username))     # black

        for proto in self.server.get_spectators():
            self.send_packet(packet.construct_person_packet(proto.id, 'S', proto.username))

        self.send_packet(packet.construct_id_packet(self.id))

        # whose turn it currently is
        self.send_packet(packet.construct_whose_turn_packet(self.server.turn))

    def PLAY(self, p: str, from_client=True):
        pid = r32_to_r10(p[0])

        if from_client:
            if pid == packet.MOVE:
                self.move(p)
            elif pid == packet.CHAT:
                self.chat(p)
        else:
            if pid == packet.PERSON:
                self.send_packet(p)
            elif pid == packet.GOODBYE:
                self.send_packet(p)
            elif pid == packet.MOVE:
                self.send_packet(p)
            elif pid == packet.WHOSETURN:
                self.send_packet(p)
            elif pid == packet.LOG:
                self.send_packet(p)

    def move(self, p: str):
        piece = p[1]
        y = r32_to_r10(p[2])
        x = r32_to_r10(p[3])

        if (y, x) in self.server.board.moveable_positions(piece):
            # good
            self.server.board.move(piece, y, x)

            self.broadcast(p, include_self=True)

            self.server.turn = 'W' if self.server.turn == 'B' else 'B'

            self.broadcast(packet.construct_whose_turn_packet(self.server.turn), include_self=True)

    def chat(self, p: str):
        """
        Broadcasts a chat message which includes this protocol's connected player name.
        Truncates to 80 characters. Cannot be empty.
        """
        message = p[1:]
        if message.strip() != '':
            message: str = f"{self.username} says: {message[:80]}"
            self.broadcast(packet.construct_log_packet(message), include_self=True)
            self.logger.log(message)
