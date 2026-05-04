from lib.parser import get_args, validate_args
import socket

from lib.protocol import Protocol

if __name__ == "__main__":
    args = get_args("upload")

    protocol = validate_args(args)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        with open(args.src, "rb") as file:
            protocol.client_send(client_socket, (args.host, args.port), file,
                                 args.name)
    except FileNotFoundError:
        print("File not found.")
    except PermissionError:
        print("Permission denied.")
    except TypeError:
        print("Filepath not specified.")
    except ConnectionError as e:
        print(f"Connection error: {e}")

    client_socket.close()
