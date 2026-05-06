from lib.settings import FAILED_TO_ESTABLISH_CONNECTION, MEDIUM_VERBOSITY, \
    HIGH_VERBOSITY
from lib.segment import Segment, SYN, ACK, FIN
from lib.metadata import Metadata
import socket
import pickle

# We use the MTU (Maximum Transmission Unit) as our segment's maximum size so
# as to avoid fragmentation in lower Internet layers.
MTU = 1500
# An MSS is the Maximum Segment Size, though it defines the maximum payload
# size. According to Kurose's book, 1460 bytes is its typical value, but we use
# less than that since out segment's header uses more than 40 bytes.
# TODO We should keep it in the highest possible value.
MAX_PAYLOAD_SIZE = 1350

MAX_TIMEOUT_HANDSHAKE = 10
MAX_RETRIES = 8
# After trying different values, this is the one that got us the best
# performance:
TIMEOUT = 0.05

class Protocol:
    def __init__(self):
        self.set_verbosity_level()

    @classmethod
    def from_str(cls, str):
        for subclass in cls.__subclasses__():
            if str == subclass.ID:
                return subclass()

    def set_verbosity_level(self, verbosity_level: int = MEDIUM_VERBOSITY):
        self.verbosity_level = verbosity_level

    def log(self, msg: str, verbosity_level: int = MEDIUM_VERBOSITY):
        if self.verbosity_level >= verbosity_level:
            print(msg)

    def _recv_segment(self, dest: socket.socket) -> Segment:
        bytes_received = bytearray(MTU)
        q_bytes_received = dest.recv_into(bytes_received)
        return pickle.loads(bytes_received[:q_bytes_received])

    def _handshake(self, origin: socket.socket, dest: tuple[str, int],
                   operation: str, filename: str):
        for attempt in range(MAX_TIMEOUT_HANDSHAKE):
            try:
                origin.sendto(pickle.dumps(
                    Segment(syn_flag=True, payload=pickle.dumps(
                        Metadata(operation, filename, self.ID)))), dest)
                bytes_received = bytearray(MTU)
                q_bytes_received, dest = origin.recvfrom_into(bytes_received)
                reply = pickle.loads(
                    bytes_received[:q_bytes_received])

                if reply.flags[ACK] and reply.flags[SYN] and reply.ack_num == 1:
                    # este último AND puede
                    # llegar a ser redundante
                    origin.connect(dest)
                    origin.send(pickle.dumps(
                        Segment(ack_flag=True, seq_num=1, ack_num=1)))
                    break

            except socket.timeout:
                self.log(f"Attempt {attempt + 1}/{MAX_TIMEOUT_HANDSHAKE} " + \
                         "failed. Retrying…")
        else:
            raise ConnectionError(FAILED_TO_ESTABLISH_CONNECTION)

    def _teardown_sender(self, sock: socket.socket, seq_num: int,
                         ) -> None:
        self.log("SENDER: Starting teardown…", HIGH_VERBOSITY)

        while True:
            sock.send(pickle.dumps(Segment(fin_flag=True, seq_num=seq_num)))
            try:
                reply = self._recv_segment(sock)
                if reply.flags[ACK] and reply.ack_num == seq_num:
                    break

                # con esto evitamos un deadlock fin - fin.
                if reply.flags[FIN]:
                    sock.send(pickle.dumps(
                        Segment(ack_flag=True, ack_num=reply.seq_num)))
                    return

            except socket.timeout:
                continue

        retries = 0
        while retries < MAX_RETRIES:
            try:
                reply = self._recv_segment(sock)
                if reply.flags[FIN]:
                    sock.send(pickle.dumps(
                        Segment(ack_flag=True, ack_num=reply.seq_num)))
                    break

            except socket.timeout:
                retries += 1
                continue

        self.log("SENDER: Teardown complete.", HIGH_VERBOSITY)

    def _teardown_recv(self, sock: socket.socket, expected_seq: int) -> None:
        self.log("RECEIVER: Starting teardown...", HIGH_VERBOSITY)

        sock.send(pickle.dumps(
            Segment(ack_flag=True, ack_num=expected_seq)))
        retries = 0

        while retries < MAX_RETRIES:
            sock.send(pickle.dumps(
                Segment(fin_flag=True, seq_num=expected_seq)))
            try:
                reply = self._recv_segment(sock)
                if reply.flags[ACK] and reply.ack_num == expected_seq:
                    break
            except socket.timeout:
                retries += 1
                continue

        self.log("RECEIVER: Teardown complete.", HIGH_VERBOSITY)
