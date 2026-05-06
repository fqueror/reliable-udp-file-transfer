from lib.settings import UPLOAD, READ_IN_BINARY_MODE, FILE_NOT_FOUND, \
    PERMISSION_DENIED, FILE_PATH_NOT_SPECIFIED
from lib.protocol.protocol import TIMEOUT
from lib.parser import get_args, validate_args
import socket


if __name__ == "__main__":
    args = get_args(UPLOAD)

    protocol = validate_args(args)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(TIMEOUT)

    try:
        with open(args.src, READ_IN_BINARY_MODE) as file:
            protocol.client_send(client_socket, (args.host, args.port), file,
                                 args.name)
    except FileNotFoundError:
        print(FILE_NOT_FOUND)
    except PermissionError:
        print(PERMISSION_DENIED)
    except TypeError:
        print(FILE_PATH_NOT_SPECIFIED)
    except ConnectionError as e:
        print(f"Connection error: {e}")

    client_socket.close()
