from lib.protocol import TIMEOUT
from lib.parser import get_args
import socket
import os

if __name__ == "__main__":
    args = get_args("download")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(TIMEOUT)

    with open(os.path.join(args.dst, args.name), "wb") as file:
        args.protocol.client_recv(client_socket, (args.host, args.port), file,
                                  args.name)

    client_socket.close()
