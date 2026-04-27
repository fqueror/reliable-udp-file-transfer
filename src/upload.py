from lib.parser import get_args
import socket

if __name__ == "__main__":
    args = get_args("upload")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.connect((args.host, args.port))
    filepath = args.src
    filename = args.name

    with open(filepath, "rb") as file:
        args.protocol.send_file(client_socket, file, filename)

    client_socket.close()
