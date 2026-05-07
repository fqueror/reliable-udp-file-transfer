from lib.settings import OP_UPLOAD, OP_DOWNLOAD, WRITE_IN_BINARY_MODE, \
    READ_IN_BINARY_MODE, LOW_VERBOSITY, MEDIUM_VERBOSITY, SERVER_DEFAULT_HOST, SERVER_DEFAULT_PORT, SERVER_DEFAULT_PATH
from lib.protocol.protocol import Protocol, MTU, TIMEOUT
from lib.segment import Segment, SYN, ACK
from lib.metadata import Metadata
import threading
import argparse
import pickle
import socket
import os


class Server:
    def __init__(self, args: argparse.Namespace):
        self.host = args.host or SERVER_DEFAULT_HOST
        self.port = args.port or SERVER_DEFAULT_PORT

        self.storage = args.storage or SERVER_DEFAULT_PATH
        os.makedirs(self.storage, exist_ok=True)

        self.verbosity_level = args.verbosity_level

        self.welcoming_socket = socket.socket(socket.AF_INET,
                                              socket.SOCK_DGRAM)
        self.welcoming_socket.bind((self.host, self.port))
        self._clients_in_progress: dict[tuple, socket.socket] = {}
        self._lock = threading.Lock()

    def log(self, msg: str, verbosity_level: int = MEDIUM_VERBOSITY):
        if self.verbosity_level >= verbosity_level:
            print(msg)

    def handle_client(self, metadata: Metadata, addr: tuple,
                      connection_socket: socket.socket):
        self.log(f"[SOCKET] Connecting with `{addr[0]}:{addr[1]}`.")

        try:
            while True:
                connection_socket.send(pickle.dumps(
                    Segment(ack_flag=True, syn_flag=True, seq_num=0,
                            ack_num=1)))
                try:
                    bytes_received = bytearray(MTU)
                    q_bytes_received = connection_socket.recv_into(
                        bytes_received)
                    reply = pickle.loads(bytes_received[:q_bytes_received])

                    if reply.flags[ACK] and reply.ack_num == 1:
                        break

                except socket.timeout:
                    continue

            protocol = Protocol.from_str(metadata.protocol)
            protocol.set_verbosity_level(self.verbosity_level)

            path = os.path.join(self.storage, str(metadata.filename))

            if metadata.operation == OP_UPLOAD:
                with open(path, WRITE_IN_BINARY_MODE) as file:
                    protocol.recv_file(connection_socket, file)
            elif metadata.operation == OP_DOWNLOAD:
                try:
                    with open(path, READ_IN_BINARY_MODE) as file:
                        protocol.send_file(connection_socket, file)
                except FileNotFoundError:
                    self.log(f"[SOCKET] `{path}` doesn't exist.", LOW_VERBOSITY)

        finally:
            with self._lock:
                self._clients_in_progress.pop(addr, None)
            connection_socket.close()

    def start(self):
        self.log("[SERVER] Server running, listening to connections at " + \
                 f"`{self.host}:{self.port}`, and saving files in directory " + \
                 f"`{self.storage}`.")
        try:
            while True:
                encoded_segment, client_addr = self.welcoming_socket.recvfrom(
                    MTU)
                segment = pickle.loads(encoded_segment)

                if not segment.flags[SYN]:
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
                    connection_socket.settimeout(TIMEOUT)
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
            self.log("\n[SERVER] Closing server.")
