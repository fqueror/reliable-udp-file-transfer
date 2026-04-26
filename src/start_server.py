from lib.parser import get_args
from lib.segment import Segment, MTU
import socket
import pickle
import os

MAX_PAYLOAD_SIZE = 1400
OP_UPLOAD = "UPLOAD"
OP_DOWNLOAD = "DOWNLOAD"

if __name__ == "__main__":
    args = get_args("start-server")

    socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket.bind((args.host, args.port))

    os.makedirs(args.storage, exist_ok=True)
    # Change the file's extension to match the one being received:
    file = open(args.storage + "/archivo_recibido.mp4", "wb")

    while True:
        # TODO Una vez tengamos el _3-way-handshake_, vamos a poder usar
        # TODO `socket.connect` para evitar tener que obtener el `client_addr`
        # TODO cada vez. O con los _threads_.

        bytes_received = bytearray(MTU * 2)  # pickle necesita mas de 1500
        q_bytes_received, client_addr = socket.recvfrom_into(bytes_received)
        segment = pickle.loads(bytes_received[:q_bytes_received])

        if segment.operation == OP_UPLOAD:

            file.write(segment.payload)

            socket.sendto(pickle.dumps(Segment(ack_flag=True)), client_addr)

            if segment.flags["FIN"]:
                break

        elif segment.operation == OP_DOWNLOAD:
            file = open(args.storage + "/archivo_a_enviar.bin", "rb")

            while (chunk := file.read(MAX_PAYLOAD_SIZE)):
                while True:
                    socket.sendto(pickle.dumps(
                        Segment(payload=chunk)), client_addr)

                    bytes_received = bytearray(MTU)
                    q_bytes_received = socket.recv_into(bytes_received)
                    reply = pickle.loads(bytes_received[:q_bytes_received])

                    if reply.flags["ACK"] is True:
                        break

            socket.sendto(pickle.dumps(Segment(fin_flag=True)), client_addr)

    socket.close()
    file.close()
