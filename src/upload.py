from lib.parser import get_args
import socket

from lib.protocol import Protocol

if __name__ == "__main__":
    args = get_args("upload")

    if args.protocol is None:
        print("Protocol not specified.")
        exit(1)
    protocol = Protocol.from_str(args.protocol)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        with open(args.src, "rb") as file:
            protocol.client_send(client_socket, (args.host, args.port), file,
                                 args.name)
    except FileNotFoundError:
        print("File not found.")

    client_socket.close()
