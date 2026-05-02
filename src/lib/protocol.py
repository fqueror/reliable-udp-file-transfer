from lib.metadata import Metadata, OP_UPLOAD, OP_DOWNLOAD
from lib.segment import Segment
import socket
import pickle
import io
import time

MTU = 5000
MAX_PAYLOAD_SIZE = 4500



class Protocol:
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
        while True:
            try:
                origin.sendto(pickle.dumps(
                    Segment(payload=pickle.dumps(
                        Metadata(operation, filename, self.ID)))), dest)
                bytes_received = bytearray(MTU)
                q_bytes_received, dest = origin.recvfrom_into(bytes_received)
                origin.connect(dest)
                if pickle.loads(
                        bytes_received[:q_bytes_received]).flags["ACK"]:
                    break
            except socket.timeout:
                continue


class StopAndWait(Protocol):
    ID = "stop-and-wait"

    def __repr__(self):
        return "Stop And Wait"

    def send_file(self, origin: socket.socket, file: io.BufferedReader):
        timeout_var = TimeoutVariable()
        origin.settimeout(timeout_var.rto)
        seq = 0
        while chunk := file.read(MAX_PAYLOAD_SIZE):
            while True:
                origin.send(pickle.dumps(Segment(seq_num=seq, payload=chunk)))
                try:
                    t_inicio = time.time()
                    reply = self._recv_segment(origin)
                    if reply.flags["ACK"] and reply.seq_num == seq:
                        rtt_muestra = time.time() - t_inicio
                        origin.settimeout(timeout_var.update(rtt_muestra))
                        seq = 1 - seq
                        break
                except socket.timeout:
                    origin.settimeout(timeout_var.on_timeout())
                    continue

        # teardown begins
        while True:
            origin.send(pickle.dumps(Segment(fin_flag=True, seq_num=seq)))
            try:
                reply = self._recv_segment(origin)
                if reply.flags["ACK"] and reply.seq_num == seq:
                    break
            except socket.timeout:
                origin.settimeout(timeout_var.on_timeout())
                continue

        while True:
            try:
                reply = self._recv_segment(origin)
                if reply.flags["FIN"]:
                    origin.send(pickle.dumps(
                        Segment(ack_flag=True, seq_num=reply.seq_num)))
                    break

            except socket.timeout:
                origin.settimeout(timeout_var.on_timeout())
                continue

    def recv_file(self, origin: socket.socket, file: io.BufferedReader):
        timeout_var = TimeoutVariable()
        origin.settimeout(timeout_var.rto)
        expected_seq = 0
        while True:
            try:
                segment = self._recv_segment(origin)
            except socket.timeout:
                origin.settimeout(timeout_var.on_timeout())
                continue

            if segment.seq_num != expected_seq:
                origin.send(pickle.dumps(
                    Segment(ack_flag=True, seq_num=1-expected_seq)))
                continue

            if segment.flags["FIN"]:
                origin.send(pickle.dumps(
                    Segment(ack_flag=True, seq_num=expected_seq)))

                while True:
                    origin.send(pickle.dumps(
                        Segment(fin_flag=True, seq_num=expected_seq)))
                    try:
                        reply = self._recv_segment(origin)
                        if reply.flags["ACK"]:
                            break
                    except socket.timeout:
                        continue

                break

            file.write(segment.payload)
            origin.send(pickle.dumps(
                Segment(ack_flag=True, seq_num=expected_seq)))
            expected_seq = 1 - expected_seq

    def client_send(self, origin: socket.socket, dest: tuple[str, int],
                    file: io.BufferedReader, filename: str):
        self._handshake(origin, dest, OP_UPLOAD, filename)
        self.send_file(origin, file)

    def client_recv(self, dest: socket.socket, origin: tuple[str, int],
                    file: io.BufferedReader, filename: str):
        self._handshake(dest, origin, OP_DOWNLOAD, filename)
        self.recv_file(dest, file)


class GoBackN(Protocol):
    ID = "go-back-n"

    def __repr__(self):
        return "Go Back N"


class TimeoutVariable():
    def __init__(self):
        self.srtt = 0.05
        self.rttvar = 0.01
        self.rto = 0.1

    def update(self, rtt_muestra):
        alpha = 0.125
        beta = 0.25
        self.srtt = (1 - alpha) * self.srtt + alpha * rtt_muestra
        self.rttvar = (1 - beta) * self.rttvar + beta * abs(self.srtt - rtt_muestra)
        self.rto = max(self.srtt + 4 * self.rttvar, 0.1)
        return self.rto

    def on_timeout(self):
        self.rto = min(self.rto * 2, 60)  # backoff exponencial, para aumentar el tiempo de espera después de cada timeout, con un límite máximo de 60 segundos
        return self.rto