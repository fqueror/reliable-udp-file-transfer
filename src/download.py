from lib.parser import get_args, validate_args
import socket
import os

if __name__ == "__main__":
    args = get_args("download")
    protocol = validate_args(args)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        with open(os.path.join(args.dst, args.name), "wb") as file:
            protocol.client_recv(client_socket, (args.host, args.port), file,
                                 args.name)
    except FileNotFoundError:
        print("Directory not found.")
    except ConnectionError as e:
        print(f"Connection error: {e}")

    client_socket.close()
