from lib.settings import DOWNLOAD, WRITE_IN_BINARY_MODE, DIRECTORY_NOT_FOUND
from lib.parser import get_args, validate_args
from lib.protocol.protocol import TIMEOUT
import socket
import os

if __name__ == "__main__":
    args = get_args(DOWNLOAD)
    protocol = validate_args(args)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(TIMEOUT)
    file_path = os.path.join(args.dst, args.name)

    try:
        with open(file_path, WRITE_IN_BINARY_MODE) as file:
            protocol.client_recv(client_socket, (args.host, args.port), file,
                                 args.name)
    except FileNotFoundError:
        print(DIRECTORY_NOT_FOUND)
    except ConnectionError as e:
        print(f"Connection error: {e}")
        if os.path.exists(file_path):
            os.remove(file_path)

    client_socket.close()
