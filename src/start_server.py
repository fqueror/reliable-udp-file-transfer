from lib.parser import get_args
import socket
import pickle
import os

# We use the MTU (Maximum Transmission Unit) as our segment's maximum size so
# as to avoid fragmentation in lower Internet layers.
MTU = 1500

if __name__ == "__main__":
    args = get_args("start-server")

    socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket.bind((args.host, args.port))

    os.makedirs(args.storage, exist_ok=True)
    # Change the file's extension to match the one being received:
    file = open(args.storage + "/archivo_recibido.mp4", "wb")

    while True:
        bytes_received = bytearray(MTU)
        q_bytes_received = socket.recv_into(bytes_received)
        segment = pickle.loads(bytes_received[:q_bytes_received])

        if segment.flags["FIN"]:
            break
        file.write(segment.payload)

    socket.close()
    file.close()
