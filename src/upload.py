from lib.parser import get_args
from lib.segment import Segment
import socket
import pickle

# An MSS is the Maximum Segment Size, though it defines the maximum payload
# size. According to Kurose's book, 1460 bytes is its typical value.
# TODO Since we use `Segment`, our header is larger than 40 bytes, and we then
# TODO must use an MSS lower than the typical. However, we should use the
# TODO highest possible one within that range. For now, 1400 does the
# TODO job, but we must check if it is the best possible value.
MAX_PAYLOAD_SIZE = 1400

if __name__ == "__main__":
    args = get_args("upload")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.connect((args.host, args.port))

    with open(args.src, "rb") as file:
        # We must separate the file in chunks because `socket.sendto` can only
        # send certain amount of bytes.
        while (chunk := file.read(MAX_PAYLOAD_SIZE)):
            client_socket.send(pickle.dumps(Segment(payload=chunk)))

    client_socket.send(pickle.dumps(Segment(fin_flag=True)))
    client_socket.close()
