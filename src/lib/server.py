from lib.constants import MTU, OP_UPLOAD, OP_DOWNLOAD
from lib.protocol import Protocol
import threading
import socket
import pickle
import queue
import os


class Server:
    def __init__(self, args):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((args.host, args.port))

        self.storage = args.storage
        os.makedirs(self.storage, exist_ok=True)

        self.clients = {}

    def handle_client(self, client_addr, client_queue):
        print(f"[NUEVO HILO] Atendiendo a {client_addr}")
        first_segment = client_queue.get()
        metadata = pickle.loads(first_segment.payload)
        protocol = Protocol.from_str(metadata.protocol)

        if metadata.operation == OP_UPLOAD:
            with open(os.path.join(self.storage, str(metadata.filename)),
                      "wb") as file:
                protocol.upload_file(file, self.socket, client_addr,
                                     client_queue)
        elif metadata.operation == OP_DOWNLOAD:
            with open(os.path.join(self.storage, str(metadata.filename)),
                      "rb") as file:
                protocol.download_file(self.socket, client_addr, client_queue,
                                       file)

        del self.clients[client_addr]

    def start(self):
        try:
            while True:
                data, addr = self.socket.recvfrom(MTU)
                segment = pickle.loads(data)

                if addr not in self.clients:
                    client_queue = queue.Queue()
                    self.clients[addr] = client_queue
                    client_queue.put(segment)
                    thread = threading.Thread(target=self.handle_client,
                                              args=(addr, client_queue))
                    thread.daemon = True
                    thread.start()

                else:
                    self.clients[addr].put(segment)
        except KeyboardInterrupt:
            self.socket.close()
            print("\n[APAGANDO] Cerrando el servidor de forma segura...")
