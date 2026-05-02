from lib.metadata import Metadata, OP_UPLOAD, OP_DOWNLOAD
from lib.segment import Segment
import socket
import pickle
import io

MTU = 1500
MAX_PAYLOAD_SIZE = 1400
TIMEOUT = 0.1


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
        origin.settimeout(TIMEOUT)
        seq = 0
        while chunk := file.read(MAX_PAYLOAD_SIZE):
            while True:
                origin.send(pickle.dumps(Segment(seq_num=seq, payload=chunk)))
                try:
                    reply = self._recv_segment(origin)
                    if reply.flags["ACK"] and reply.seq_num == seq:
                        seq = 1 - seq
                        break
                except socket.timeout:
                    continue

        # teardown begins
        while True:
            origin.send(pickle.dumps(Segment(fin_flag=True, seq_num=seq)))
            try:
                reply = self._recv_segment(origin)
                if reply.flags["ACK"] and reply.seq_num == seq:
                    break
            except socket.timeout:
                continue

        while True:
            try:
                reply = self._recv_segment(origin)
                if reply.flags["FIN"]:
                    origin.send(pickle.dumps(
                        Segment(ack_flag=True, seq_num=reply.seq_num)))
                    break

            except socket.timeout:
                continue

    def recv_file(self, origin: socket.socket, file: io.BufferedReader):
        origin.settimeout(TIMEOUT)
        expected_seq = 0
        while True:
            try:
                segment = self._recv_segment(origin)
            except socket.timeout:
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
        while True:
            try:
                origin.sendto(pickle.dumps(
                    Segment(payload=pickle.dumps(
                        Metadata(OP_UPLOAD, filename, self.ID)))), dest)
                bytes_received = bytearray(MTU)
                q_bytes_received, dest = origin.recvfrom_into(bytes_received)
                origin.connect(dest)
                if pickle.loads(
                        bytes_received[:q_bytes_received]).flags["ACK"]:
                    break
            except socket.timeout:
                continue

        self.send_file(origin, file)

    def client_recv(self, dest: socket.socket, origin: tuple[str, int],
                    file: io.BufferedReader, filename: str):
        while True:
            try:
                dest.sendto(pickle.dumps(
                    Segment(payload=pickle.dumps(
                        Metadata(OP_DOWNLOAD, filename, self.ID)))), origin)
                bytes_received = bytearray(MTU)
                q_bytes_received, origin = dest.recvfrom_into(bytes_received)
                dest.connect(origin)
                if pickle.loads(
                        bytes_received[:q_bytes_received]).flags["ACK"]:
                    break

            except socket.timeout:
                continue

        self.recv_file(dest, file)


class GoBackN(Protocol):
    ID = "go-back-n"

    def __repr__(self):
        return "Go Back N"
