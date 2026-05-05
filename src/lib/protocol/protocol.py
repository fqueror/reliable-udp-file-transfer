
from lib.settings import MTU, MAX_TIMEOUT_HANDSHAKE, ACK, FIN, SRTT, RTTVAR, RTO, ALPHA, BETA, SEC_TIMEOUT_LIMIT, \
    MAX_RETRIES
from lib.metadata import Metadata
from lib.segment import Segment
import socket
import pickle

class TimeoutVariable():
    def __init__(self):
        self.srtt = SRTT
        self.rttvar = RTTVAR
        self.rto = RTO

    def update(self, rtt_muestra):
        self.srtt = (1 - ALPHA) * self.srtt + ALPHA * rtt_muestra
        self.rttvar = (1 - BETA) * self.rttvar + BETA * \
            abs(self.srtt - rtt_muestra)
        self.rto = max(self.srtt + 4 * self.rttvar, 0.1)
        return self.rto

    def on_timeout(self):
        # backoff exponencial, para aumentar el tiempo de espera después
        # de cada timeout, con un límite máximo de 60 segundos
        self.rto = min(self.rto * 2, SEC_TIMEOUT_LIMIT)
        return self.rto

class Protocol:
    def __init__(self, verbose: bool = False, quiet: bool = False):
        self.verbose = verbose
        self.quiet = quiet

    def log(self, message: str, is_verbose: bool = False):
        if self.quiet:
            return
        if is_verbose and not self.verbose:
            return
        print(message)

    @classmethod
    def from_str(cls, str):
        for subclass in cls.__subclasses__():
            if str == subclass.ID:
                return subclass()

    def _recv_segment(self, dest: socket.socket) -> Segment:
        bytes_received = bytearray(MTU)
        q_bytes_received = dest.recv_into(bytes_received)
        return pickle.loads(bytes_received[:q_bytes_received])

    def _handshake(self, origin: socket.socket,
                   dest: tuple[str, int],
                   operation: str,
                   filename: str):

        for attempt in range(MAX_TIMEOUT_HANDSHAKE):
            try:
                origin.sendto(pickle.dumps(
                    Segment(syn_flag=True, payload=pickle.dumps(
                        Metadata(operation, filename, self.ID)))), dest)
                bytes_received = bytearray(MTU)
                q_bytes_received, dest = origin.recvfrom_into(bytes_received)
                reply = pickle.loads(
                    bytes_received[:q_bytes_received])

                if reply.flags[ACK] and reply.flags["SYN"] \
                        and reply.ack_num == 1:
                    # este último AND puede
                    # llegar a ser redundante
                    origin.connect(dest)
                    origin.send(pickle.dumps(
                        Segment(ack_flag=True, seq_num=1, ack_num=1)))
                    break

            except socket.timeout:
                self.log(
                    f"Attempt {
                        attempt + 1}/{MAX_TIMEOUT_HANDSHAKE} failed. Retrying...")

        raise ConnectionError("Failed to establish connection.")

    def _teardown_sender(self, sock: socket.socket, seq_num: int,
                         ) -> None:
        self.log("SENDER: Starting teardown...", is_verbose=True)

        while True:
            sock.send(pickle.dumps(Segment(fin_flag=True, seq_num=seq_num)))
            try:
                reply = self._recv_segment(sock)
                if reply.flags[ACK] and reply.ack_num == seq_num:
                    break

                # con esto evitamos un deadlock fin - fin.
                if reply.flags["FIN"]:
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

        self.log("SENDER: Teardown complete.", is_verbose=True)

    def _teardown_recv(self, sock: socket.socket, expected_seq: int) -> None:
        self.log("RECEIVER: Starting teardown...", is_verbose=True)

        sock.send(pickle.dumps(
            Segment(ack_flag=True, ack_num=expected_seq)))
        retries = 0

        while retries < MAX_RETRIES:
            sock.send(pickle.dumps(
                Segment(fin_flag=True, seq_num=expected_seq)))
            try:
                reply = self._recv_segment(sock)
                if reply.flags["ACK"] and reply.ack_num == expected_seq:
                    break
            except socket.timeout:
                retries += 1
                continue

        self.log("RECEIVER: Teardown complete.", is_verbose=True)

