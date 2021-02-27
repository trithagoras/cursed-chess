import curses
import os
import sys

# Required to import top level modules
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

from client.state import ClientState

if __name__ == '__main__':
    # Eliminate delay in the program after the ESC key is pressed
    os.environ.setdefault('ESCDELAY', '25')

    curses.wrapper(ClientState)
    pass
