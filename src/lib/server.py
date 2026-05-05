import threading
import argparse
import socket
import pickle
import os

from lib.metadata import Metadata
from lib.settings import OP_UPLOAD, OP_DOWNLOAD, MAX_ATTEMPTS, SERVER_DEFAULT_HOST, SERVER_DEFAULT_PORT, \
    SERVER_DEFAULT_STORAGE, FILE_WRITER, FILE_READER, FILE_NOT_FOUND, ACK, TIMEOUT, SYN
from lib.protocol.protocol import Protocol, MTU
from lib.segment import Segment


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
        self._clients_in_progress: dict[tuple, socket.socket] = {}
        self._lock = threading.Lock()

    def config_server(self, args: argparse.Namespace):
        self.host = args.host or SERVER_DEFAULT_HOST
        self.port = args.port or SERVER_DEFAULT_PORT
        self.storage = args.storage or SERVER_DEFAULT_STORAGE
        os.makedirs(self.storage, exist_ok=True)

    def log(self, message: str, is_verbose: bool = False):
        if self.quiet:
            return
        if is_verbose and not self.verbose:
            return
        print(message)

    def handle_client(self, metadata: Metadata, addr: tuple,
                      connection_socket: socket.socket):
        self.log(f"[SOCKET] Listening to {addr}")

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
            protocol.verbose = self.verbose
            protocol.quiet = self.quiet

            path = os.path.join(self.storage, str(metadata.filename))

            if metadata.operation == OP_UPLOAD:
                with open(path, FILE_WRITER) as file:
                    protocol.recv_file(connection_socket, file)
            elif metadata.operation == OP_DOWNLOAD:
                try:
                    with open(path, FILE_READER) as file:
                        protocol.send_file(connection_socket, file)
                except FileNotFoundError:
                    segment = Segment(
                        error_flag=True,
                        payload=pickle.dumps(FILE_NOT_FOUND))
                    for attempt in range(MAX_ATTEMPTS):
                        try:
                            connection_socket.send(pickle.dumps(segment))
                            ack = pickle.loads(connection_socket.recv(MTU))
                            if ack.flags[ACK]:
                                self.log(
                                    f"File not found. Client {addr} notified.")
                                break
                        except socket.timeout:
                            continue
                    connection_socket.close()

        finally:
            with self._lock:
                self._clients_in_progress.pop(addr, None)
            connection_socket.close()

    def start(self):
        self.log(
            f"[SERVER] Running server in {
                self.host}:{
                self.port} and storing in path {
                self.storage}")
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
