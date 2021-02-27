import curses
import curses.ascii
import sys

from client.controllers.controller import Controller
from client.controllers.widgets import Button, TextField
from client.views.menuviews import MainMenuView, UsernameView
from networking import packet


class Menu(Controller):
    def __init__(self, cs):
        super().__init__(cs)
        self.cursor = 0

    def process_input(self, key: int):
        for widget in self.widgets:
            if widget.selected:
                widget.process_input(key)
                return

        # menu controls
        if key == curses.KEY_UP:
            self.cursor = max(0, self.cursor - 1)
        elif key == curses.KEY_DOWN:
            self.cursor = min(len(self.widgets) - 1, self.cursor + 1)
        elif key == ord('\n'):      # enter key
            self.widgets[self.cursor].select()
        elif curses.ascii.isprint(key):
            if isinstance(self.widgets[self.cursor], TextField):
                field = self.widgets[self.cursor]
                field.value = chr(key)
                field.cursor = 1
                field.select()
        elif key == curses.ascii.ESC:
            self.process_exit()


class MainMenu(Menu):
    def __init__(self, cs):
        super().__init__(cs)
        self.view = MainMenuView(self)

        self.widgets.append(TextField(self, title="Host: "))
        self.widgets.append(TextField(self, title="Port: "))
        self.widgets.append(Button(self, "Connect", self.connect))

        self.view.place_widget(self.widgets[0], 10, 10)
        self.view.place_widget(self.widgets[1], 14, 10)
        self.view.place_widget(self.widgets[2], 18, 10)

    def connect(self):
        host = self.widgets[0].value
        port = self.widgets[1].value

        if "" in (host, port):
            self.view.title = "Username or password must not be blank"
            return

        if not self.cs.ns.connect(host, port):
            self.view.title = "Connection failed. Is the server up?"

    def process_packet(self, p) -> bool:
        pid = packet.r32_to_r10(p[0])

        if pid == packet.OK:
            self.cs.change_controller("UsernameMenu")
        elif pid == packet.NO:
            self.view.title = p[1:]
        else:
            return False

        return True

    def process_exit(self):
        sys.exit(0)


class UsernameMenu(Menu):
    def __init__(self, cs):
        super().__init__(cs)
        self.view = UsernameView(self)

        self.widgets.append(TextField(self, title="Username: "))
        self.widgets.append(Button(self, "Accept", self.accept))

        self.view.place_widget(self.widgets[0], 10, 10)
        self.view.place_widget(self.widgets[1], 14, 10)

    def accept(self):
        username = self.widgets[0].value

        if not username:
            self.view.title = "Username cannot be blank"
            return

        self.cs.ns.send_packet(packet.construct_username_packet(username))

    def process_packet(self, p) -> bool:
        pid = packet.r32_to_r10(p[0])

        if pid == packet.OK:
            self.cs.change_controller("Game")
        elif pid == packet.NO:
            self.view.title = p[1:]
        else:
            return False

        return True

    def process_exit(self):
        self.cs.ns.disconnect()
        self.cs.change_controller("MainMenu")
