from lib.parser import get_args
import socket

if __name__ == "__main__":
    args = get_args("download")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.connect((args.host, args.port))
    filename = args.name

    with open(args.dst / filename, "wb") as file:
        args.protocol.receive_file(client_socket, file, filename)

    client_socket.close()
