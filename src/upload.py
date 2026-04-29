from lib.parser import get_args
import socket

if __name__ == "__main__":
    args = get_args("upload")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.connect((args.host, args.port))

    with open(args.src, "rb") as file:
        args.protocol.client_send(client_socket, file, args.name)

    client_socket.close()
