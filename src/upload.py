from lib.parser import get_args
import socket

# An MSS is the Maximum Segment Size, though it defines the maximum payload
# size. According to Kurose's book, 1460 bytes is its typical value.
MAX_PAYLOAD_SIZE = 1460

if __name__ == "__main__":
    args = get_args("upload")
    server_addr = (args.host, args.port)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    with open(args.src, "rb") as file:
        # We must separate the file in chunks because `socket.sendto` can only
        # send certain amount of bytes.
        while (chunk := file.read(MAX_PAYLOAD_SIZE)):
            client_socket.sendto(chunk, server_addr)

    client_socket.sendto(b"__END__", server_addr)

    client_socket.close()
