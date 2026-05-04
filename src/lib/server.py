from lib.metadata import Metadata, OP_UPLOAD, OP_DOWNLOAD
from lib.protocol import Protocol, MTU
from lib.segment import Segment
import threading
import argparse
import socket
import pickle
import os

TIMEOUT = 0.1


class Server:
    def __init__(self, args: argparse.Namespace):
        self.welcoming_socket = socket.socket(socket.AF_INET,
                                              socket.SOCK_DGRAM)
        self.welcoming_socket.bind((args.host, args.port))

        self.storage = args.storage
        os.makedirs(self.storage, exist_ok=True)

    def handle_client(self, metadata: Metadata, addr: str):
        print(f"[NUEVO HILO] Atendiendo a {addr}")
        connection_socket = socket.socket(socket.AF_INET,
                                          socket.SOCK_DGRAM)
        connection_socket.connect(addr)
        # Because of the already-received metadata segment:

        connection_socket.settimeout(TIMEOUT)

        while True:
            connection_socket.send(pickle.dumps(
                Segment(ack_flag=True, syn_flag=True, seq_num=0, ack_num=1)))
            try:
                bytes_received = bytearray(MTU)
                q_bytes_received = connection_socket.recv_into(bytes_received)
                reply = pickle.loads(bytes_received[:q_bytes_received])

                if reply.flags["ACK"] and reply.ack_num == 1:
                    break

            except socket.timeout:
                continue

        protocol = Protocol.from_str(metadata.protocol)
        path = os.path.join(self.storage, str(metadata.filename))

        if metadata.operation == OP_UPLOAD:
            with open(path, "wb") as file:
                protocol.recv_file(connection_socket, file)
        elif metadata.operation == OP_DOWNLOAD:
            with open(path, "rb") as file:
                protocol.send_file(connection_socket, file)

    def start(self):
        try:
            while True:
                encoded_segment, client_addr = self.welcoming_socket.recvfrom(
                    MTU)
                segment = pickle.loads(encoded_segment)

                if not segment.flags["SYN"]:
                    continue

                metadata = pickle.loads(segment.payload)
                thread = threading.Thread(target=self.handle_client,
                                          args=(metadata, client_addr))
                thread.daemon = True
                thread.start()

        except KeyboardInterrupt:
            self.welcoming_socket.close()
            print("\n[APAGANDO] Cerrando el servidor de forma segura...")
