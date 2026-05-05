from lib.settings import MTU, MAX_TIMEOUT_HANDSHAKE
from lib.metadata import Metadata
from lib.segment import Segment
import socket
import pickle


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
        timeout_var = TimeoutVariable()
        origin.settimeout(timeout_var.rto)

        for attempt in range(MAX_TIMEOUT_HANDSHAKE):
            try:
                origin.sendto(pickle.dumps(
                    Segment(payload=pickle.dumps(
                        Metadata(operation, filename, self.ID)))), dest)
                bytes_received = bytearray(MTU)
                q_bytes_received, dest = origin.recvfrom_into(bytes_received)
                origin.connect(dest)
                if pickle.loads(
                        bytes_received[:q_bytes_received]).flags["ACK"]:
                    return
            except socket.timeout:
                self.log(
                    f"Intento {
                        attempt + 1}/{MAX_TIMEOUT_HANDSHAKE} fallido. Reintentando...")

        raise ConnectionError("Failed to establish connection.")

    def _teardown_sender(self, sock: socket.socket, seq_num: int,
                         timeout_var) -> None:
        self.log("SENDER: Starting teardown...", is_verbose=True)

        while True:
            sock.send(pickle.dumps(Segment(fin_flag=True, seq_num=seq_num)))
            try:
                reply = self._recv_segment(sock)
                if reply.flags["ACK"] and reply.ack_num == seq_num:
                    break
            except socket.timeout:
                sock.settimeout(timeout_var.on_timeout())
                continue

        while True:
            try:
                reply = self._recv_segment(sock)
                if reply.flags["FIN"]:
                    sock.send(pickle.dumps(
                        Segment(ack_flag=True, ack_num=reply.seq_num)))
                    break

            except socket.timeout:
                sock.settimeout(timeout_var.on_timeout())
                continue

        self.log("SENDER: Teardown complete.", is_verbose=True)

    def _teardown_recv(self, sock: socket.socket, expected_seq: int,
                       timeout_var) -> None:
        self.log("RECEIVER: Starting teardown...", is_verbose=True)

        sock.send(pickle.dumps(
            Segment(ack_flag=True, ack_num=expected_seq)))

        while True:
            sock.send(pickle.dumps(
                Segment(fin_flag=True, seq_num=expected_seq)))
            try:
                reply = self._recv_segment(sock)
                if reply.flags["ACK"] and reply.ack_num == expected_seq:
                    break
            except socket.timeout:
                timeout_var.on_timeout()
                continue

        self.log("RECEIVER: Teardown complete.", is_verbose=True)


class TimeoutVariable():
    def __init__(self):
        self.srtt = 0.05
        self.rttvar = 0.01
        self.rto = 0.1

    def update(self, rtt_muestra):
        alpha = 0.125
        beta = 0.25
        self.srtt = (1 - alpha) * self.srtt + alpha * rtt_muestra
        self.rttvar = (1 - beta) * self.rttvar + beta * \
            abs(self.srtt - rtt_muestra)
        self.rto = max(self.srtt + 4 * self.rttvar, 0.1)
        return self.rto

    def on_timeout(self):
        # backoff exponencial, para aumentar el tiempo de espera después
        # de cada timeout, con un límite máximo de 60 segundos
        self.rto = min(self.rto * 2, 60)
        return self.rto
