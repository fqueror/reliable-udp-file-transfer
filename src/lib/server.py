from lib.metadata import Metadata, OP_UPLOAD, OP_DOWNLOAD
from lib.protocol import Protocol, MTU
import threading
import argparse
import socket
import pickle
import os


class Server:
    def __init__(self, args: argparse.Namespace):
        self.welcoming_socket = socket.socket(socket.AF_INET,
                                              socket.SOCK_DGRAM)
        self.welcoming_socket.bind((args.host, args.port))

        self.storage = args.storage
        os.makedirs(self.storage, exist_ok=True)

        self.clients = {}

    def handle_client(self, metadata: Metadata, addr: str):
        print(f"[NUEVO HILO] Atendiendo a {addr}")
        connection_socket = socket.socket(socket.AF_INET,
                                          socket.SOCK_DGRAM)
        connection_socket.connect(addr)

        protocol = Protocol.from_str(metadata.protocol)
        path = os.path.join(self.storage, str(metadata.filename))

        if metadata.operation == OP_UPLOAD:
            with open(path, "wb") as file:
                protocol.server_recv(file, connection_socket)
        elif metadata.operation == OP_DOWNLOAD:
            with open(path, "rb") as file:
                protocol.server_send(connection_socket, file)

    def start(self):
        try:
            while True:
                encoded_segment, client_addr = self.welcoming_socket.recvfrom(
                    MTU)
                metadata = pickle.loads(pickle.loads(encoded_segment).payload)

                thread = threading.Thread(target=self.handle_client,
                                          args=(metadata, client_addr))
                thread.daemon = True
                thread.start()

        except KeyboardInterrupt:
            self.welcoming_socket.close()
            print("\n[APAGANDO] Cerrando el servidor de forma segura...")
