from lib.parser import get_args
from lib.segment import Segment, MTU
import socket
import pickle
import os

from lib.server import Server

MAX_PAYLOAD_SIZE = 1400
OP_UPLOAD = "UPLOAD"
OP_DOWNLOAD = "DOWNLOAD"

if __name__ == "__main__":
    args = get_args("start-server")

    server = Server()
    server.config_server(args)
    server.start_server()
