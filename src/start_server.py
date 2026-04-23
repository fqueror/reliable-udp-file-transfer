from lib.parser import get_args
import socket
from lib.server import Server

if __name__ == "__main__":
    args = get_args("start-server")

    server = Server
    server.start_server()



