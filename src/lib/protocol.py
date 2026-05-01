from lib.metadata import Metadata, OP_UPLOAD, OP_DOWNLOAD
from lib.segment import Segment
import socket
import pickle
import io

MTU = 1500
MAX_PAYLOAD_SIZE = 1400


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


class StopAndWait(Protocol):
    ID = "stop-and-wait"

    def __repr__(self):
        return "Stop And Wait"

    def send_file(self, origin: socket.socket, file: io.BufferedReader):
        origin.settimeout(0.5)
        seq = 0
        while chunk := file.read(MAX_PAYLOAD_SIZE):
            while True:
                origin.send(pickle.dumps(Segment(payload=chunk, seq_num=seq)))
                try:
                    if self._recv_segment(origin).flags["ACK"]:
                        seq = 1 - seq
                        break
                except socket.timeout:
                    continue

        # FIN con confirmación
        while True:
            origin.send(pickle.dumps(Segment(fin_flag=True)))
            try:
                if self._recv_segment(origin).flags["ACK"]:
                    break
            except socket.timeout:
                continue

    def recv_file(self, origin: socket.socket, file: io.BufferedReader):
        origin.settimeout(0.5)
        expected_seq = 0
        ack = pickle.dumps(Segment(ack_flag=True))
        while True:
            try:
                segment = self._recv_segment(origin)
            except socket.timeout:
                continue

            if segment.flags["FIN"]:
                origin.send(pickle.dumps(Segment(ack_flag=True, fin_flag=True)))
                break

            if segment.seq_num == expected_seq:
                file.write(segment.payload)
                expected_seq = 1 - expected_seq

            origin.send(ack)  # siempre manda ACK

    def client_send(self, origin: socket.socket, dest: tuple[str, int],
                    file: io.BufferedReader, filename: str):
        while True:
            origin.sendto(pickle.dumps(
                Segment(payload=pickle.dumps(
                    Metadata(OP_UPLOAD, filename, self.ID)))), dest)
            bytes_received = bytearray(MTU)
            q_bytes_received, dest = origin.recvfrom_into(bytes_received)
            origin.connect(dest)
            if pickle.loads(bytes_received[:q_bytes_received]).flags["ACK"]:
                break

        self.send_file(origin, file)

    def client_recv(self, dest: socket.socket, origin: tuple[str, int],
                    file: io.BufferedReader, filename: str):
        while True:
            dest.sendto(pickle.dumps(
                Segment(payload=pickle.dumps(
                    Metadata(OP_DOWNLOAD, filename, self.ID)))), origin)
            bytes_received = bytearray(MTU)
            q_bytes_received, origin = dest.recvfrom_into(bytes_received)
            dest.connect(origin)
            if pickle.loads(bytes_received[:q_bytes_received]).flags["ACK"]:
                break

        self.recv_file(dest, file)


class GoBackN(Protocol):
    ID = "go-back-n"

    def __repr__(self):
        return "Go Back N"