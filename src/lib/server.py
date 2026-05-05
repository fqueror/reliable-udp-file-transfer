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
        self._clients_in_progress: dict[tuple, socket.socket] = {}
        self._lock = threading.Lock()

    def handle_client(self, metadata: Metadata, addr: tuple,
                      connection_socket: socket.socket):
        print(f"[NUEVO HILO] Atendiendo a {addr}")

        try:
            while True:
                connection_socket.settimeout(TIMEOUT)
                connection_socket.send(pickle.dumps(
                    Segment(ack_flag=True, syn_flag=True, seq_num=0,
                            ack_num=1)))
                try:
                    bytes_received = bytearray(MTU)
                    q_bytes_received = connection_socket.recv_into(
                        bytes_received)
                    reply = pickle.loads(bytes_received[:q_bytes_received])

                    if reply.flags["ACK"] and reply.ack_num == 1:
                        break
                    else:
                        print(
                            f"[SERVER] Segmento inesperado en handshake: flags=\
                            {reply.flags}, ack_num={reply.ack_num}")

                except socket.timeout:
                    continue

            print(f"[SERVER] Handshake completo con {addr}")
            protocol = Protocol.from_str(metadata.protocol)
            path = os.path.join(self.storage, str(metadata.filename))

            if metadata.operation == OP_UPLOAD:
                with open(path, "wb") as file:
                    protocol.recv_file(connection_socket, file)
            elif metadata.operation == OP_DOWNLOAD:
                with open(path, "rb") as file:
                    protocol.send_file(connection_socket, file)

        finally:
            with self._lock:
                self._clients_in_progress.pop(addr, None)
            connection_socket.close()

    def start(self):
        try:
            while True:
                encoded_segment, client_addr = self.welcoming_socket.recvfrom(
                    MTU)
                segment = pickle.loads(encoded_segment)

                if not segment.flags["SYN"]:
                    continue

                with self._lock:
                    client_already_existing = self._clients_in_progress.get(
                        client_addr)

                    if client_already_existing:
                        client_already_existing.send(pickle.dumps(
                            Segment(syn_flag=True, ack_flag=True,
                                    seq_num=0, ack_num=1)))
                        continue

                    connection_socket = socket.socket(
                        socket.AF_INET, socket.SOCK_DGRAM)
                    connection_socket.connect(client_addr)
                    self._clients_in_progress[client_addr] = connection_socket

                metadata = pickle.loads(segment.payload)
                thread = threading.Thread(target=self.handle_client,
                                          args=(metadata, client_addr,
                                                connection_socket))
                thread.daemon = True
                thread.start()

        except KeyboardInterrupt:
            self.welcoming_socket.close()
            print("\n[APAGANDO] Cerrando el servidor de forma segura...")
