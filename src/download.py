from lib.settings import DOWNLOAD, WRITE_IN_BINARY_MODE
from lib.parser import get_args, validate_args
from lib.protocol.protocol import TIMEOUT
import socket
import os

if __name__ == "__main__":
    args = get_args(DOWNLOAD)
    protocol = validate_args(args)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(TIMEOUT)

    os.makedirs(args.dst, exist_ok=True)
    file_path = os.path.join(args.dst, args.name)

    try:
        with open(file_path, WRITE_IN_BINARY_MODE) as file:
            protocol.client_recv(client_socket, (args.host, args.port), file,
                                 args.name)
    except:
        # Ante cualquier error que haya ocurrido, eliminamos el archivo que se
        # intentó descargar:
        os.remove(file_path)
        # Pero además, si la carpeta donde lo estábamos guardando quedó vacía,
        # la eliminamos también:
        try:
            os.rmdir(args.dst)
        except OSError:
            pass

    client_socket.close()
