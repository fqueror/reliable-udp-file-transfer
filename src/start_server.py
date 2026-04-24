from lib.parser import get_args
import socket


if __name__ == "__main__":
    args = get_args("start-server")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((args.host, args.port))

    # Change the file's extension to match the one being received:
    file = open("archivo_recibido.mp4", "wb")

    while True:
        bytes_received = bytearray(4096)  # TODO Why 4096?
        q_bytes_received = server_socket.recv_into(bytes_received)

        if bytes_received[:q_bytes_received] == b"__END__":
            break
        file.write(bytes_received[:q_bytes_received])

    server_socket.close()
    file.close()
