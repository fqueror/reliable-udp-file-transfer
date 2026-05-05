from lib.metadata import Metadata, OP_UPLOAD, OP_DOWNLOAD
from lib.protocol import Protocol, MTU
from lib.segment import Segment
import threading
import argparse
import socket
import pickle
import os

MAX_ATTEMPTS = 3

class Server:
    def __init__(self, args: argparse.Namespace):
        self.host = None
        self.port = None
        self.storage = None
        self.verbose = args.verbose
        self.quiet = args.quiet

        self.config_server(args)

        self.welcoming_socket = socket.socket(socket.AF_INET,
                                              socket.SOCK_DGRAM)
        self.welcoming_socket.bind((self.host, self.port))


    def config_server(self, args: argparse.Namespace):
        self.host = args.host or "0.0.0.0"
        self.port = args.port or 12000
        self.storage = args.storage or "./storage"
        os.makedirs(self.storage, exist_ok=True)

    def log(self, message: str, is_verbose: bool = False):
        if self.quiet:
            return
        if is_verbose and not self.verbose:
            return
        print(message)

    def handle_client(self, metadata: Metadata, addr: str):
        self.log(f"[NUEVO HILO] Atendiendo a {addr}")
        connection_socket = socket.socket(socket.AF_INET,
                                          socket.SOCK_DGRAM)
        connection_socket.connect(addr)
        connection_socket.send(pickle.dumps(Segment(ack_flag=True)))

        protocol = Protocol.from_str(metadata.protocol)
        protocol.verbose = self.verbose
        protocol.quiet = self.quiet

        path = os.path.join(self.storage, str(metadata.filename))

        if metadata.operation == OP_UPLOAD:
            with open(path, "wb") as file:
                protocol.recv_file(connection_socket, file)
        elif metadata.operation == OP_DOWNLOAD:
            try:
                with open(path, "rb") as file:
                    protocol.send_file(connection_socket, file)
            except FileNotFoundError:
                segment = Segment(error_flag=True, payload=pickle.dumps("File not found"))
                for attempt in range(MAX_ATTEMPTS):
                    try:
                        connection_socket.send(pickle.dumps(segment))
                        ack = pickle.loads(connection_socket.recv(MTU))
                        if ack.flags["ACK"]:
                            self.log(f"File not found. Client {addr} notified.")
                            break
                    except socket.timeout:
                        continue
                connection_socket.close()


    def start(self):
        self.log(f"[INICIANDO] Servidor en {self.host}:{self.port} y almacenando en {self.storage}")
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
            self.log("\n[APAGANDO] Cerrando el servidor de forma segura...")
