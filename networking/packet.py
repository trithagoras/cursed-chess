
from networking.utils import *


OK = 0
NO = 1
MOVE = 2
CHAT = 3
USERNAME = 4
BOARD_STATE = 5
PERSON = 6
ID = 7
GOODBYE = 8
WHOSETURN = 9
LOG = 10


def construct_ok_packet():
    return f"{r10_to_r32(OK)}"


def construct_no_packet(reason: str):
    return f"{r10_to_r32(NO)}{reason}"


def construct_move_packet(piece_id: int, row: int, col: int):
    return f"{r10_to_r32(MOVE)}{r10_to_r32(piece_id)}{r10_to_r32(row)}{r10_to_r32(col)}"


def construct_chat_packet(message: str):
    return f"{r10_to_r32(CHAT)}{message}"


def construct_username_packet(username: str):
    return f"{r10_to_r32(USERNAME)}{username}"


def construct_board_state_packet(board_state: str):
    return f"{r10_to_r32(BOARD_STATE)}{board_state}"


def construct_id_packet(id: int):
    return f"{r10_to_r32(ID)}{r10_to_r32(id)}"


def construct_person_packet(id: int, role: str, username: str):
    """role should be W | B | S if white, black, or spectator"""
    return f"{r10_to_r32(PERSON)}{r10_to_r32(id)}{role}{username}"


def construct_goodbye_packet(id: int):
    return f"{r10_to_r32(GOODBYE)}{r10_to_r32(id)}"


def construct_whose_turn_packet(who: str):
    """who should be W | B"""
    return f"{r10_to_r32(WHOSETURN)}{who}"


def construct_log_packet(log: str):
    return f"{r10_to_r32(LOG)}{log}"
