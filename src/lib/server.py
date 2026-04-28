import socket
import pickle
import threading
import queue
import os

from lib.protocol import Protocol
from lib.constants import MTU, OP_UPLOAD, OP_DOWNLOAD


class Server:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 12000
        self.socket = None
        self.storage = ""
        # Lista de clientes activos. Cada cliente tiene su cola
        self.active_transfers = {}

    def config_server(self, args):
        self.host = args.host
        self.port = args.port
        self.storage = args.storage
        os.makedirs(self.storage, exist_ok=True)

    def handle_client(self, client_addr, client_queue):
        print(f"[NUEVO HILO] Atendiendo a {client_addr}")
        first_segment = client_queue.get()
        metadata = pickle.loads(first_segment.payload)
        protocol = Protocol.from_str(metadata.protocol)
        filename = metadata.filename

        if metadata.operation == OP_UPLOAD:
            protocol.upload_file(
                self.socket, client_addr, client_queue, self.storage, filename
            )
        elif metadata.operation == OP_DOWNLOAD:
            protocol.download_file(
                self.socket, client_addr, client_queue, self.storage, filename
            )

        del self.active_transfers[client_addr]

    def start_server(self):
        print(f"ARRANCO EL SERVIDOR en {self.host}:{self.port}")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))

        try:
            while True:
                data, addr = self.socket.recvfrom(MTU)
                segment = pickle.loads(data)

                if addr not in self.active_transfers:
                    client_queue = queue.Queue()
                    self.active_transfers[addr] = client_queue
                    client_queue.put(segment)
                    thread = threading.Thread(
                        target=self.handle_client, args=(addr, client_queue)
                    )
                    thread.daemon = True
                    thread.start()

                else:
                    self.active_transfers[addr].put(segment)
        except KeyboardInterrupt:
            self.socket.close()
            print("\n[APAGANDO] Cerrando el servidor de forma segura...")
