from twisted.internet import reactor
import sys

# Required to import top level modules
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

from server.mainserver import ChessServer


if __name__ == '__main__':
    print(f"Starting local chess server")
    PORT: int = 42523
    reactor.listenTCP(PORT, ChessServer())
    print(f"Server listening on port {42523}")
    reactor.run()
