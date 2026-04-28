from lib.parser import get_args
import socket

if __name__ == "__main__":
    args = get_args("download")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.connect((args.host, args.port))

    with open(args.dst / args.name, "wb") as file:
        args.protocol.receive_file(client_socket, file, args.name)

    client_socket.close()
