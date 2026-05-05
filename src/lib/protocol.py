from lib.metadata import Metadata, OP_UPLOAD, OP_DOWNLOAD
from lib.segment import Segment
import socket
import pickle
import select
import time
import io

# We use the MTU (Maximum Transmission Unit) as our segment's maximum size so
# as to avoid fragmentation in lower Internet layers.
MTU = 1500
# An MSS is the Maximum Segment Size, though it defines the maximum payload
# size. According to Kurose's book, 1460 bytes is its typical value, but we use
# less than that since out segment's header uses more than 40 bytes.
# TODO We should keep it in the highest possible value.
MAX_PAYLOAD_SIZE = 1350

MAX_RETRIES = 5
# After trying different values, this is the one that got us the best
# performance:
TIMEOUT = 0.05


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

    def _handshake(self, origin: socket.socket, dest: tuple[str, int],
                   operation: str, filename: str):
        while True:
            try:
                origin.sendto(pickle.dumps(
                    Segment(syn_flag=True, payload=pickle.dumps(
                        Metadata(operation, filename, self.ID)))), dest)

                bytes_received = bytearray(MTU)
                q_bytes_received, dest = origin.recvfrom_into(bytes_received)
                reply = pickle.loads(
                    bytes_received[:q_bytes_received])

                if reply.flags["ACK"] and reply.flags["SYN"] \
                        and reply.ack_num == 1:
                    # este último AND puede
                    # llegar a ser redundante
                    origin.connect(dest)
                    origin.send(pickle.dumps(
                        Segment(ack_flag=True, seq_num=1, ack_num=1)))
                    break

            except socket.timeout:
                continue

    def _teardown_sender(self, sock: socket.socket, seq_num: int) -> None:
        while True:
            sock.send(pickle.dumps(Segment(fin_flag=True, seq_num=seq_num)))
            try:
                reply = self._recv_segment(sock)
                if reply.flags["ACK"] and reply.ack_num == seq_num:
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
                if reply.flags["FIN"]:
                    sock.send(pickle.dumps(
                        Segment(ack_flag=True, ack_num=reply.seq_num)))
                    break

            except socket.timeout:
                retries += 1
                continue

    def _teardown_recv(self, sock: socket.socket, expected_seq: int) -> None:
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


class StopAndWait(Protocol):
    ID = "stop-and-wait"

    def __repr__(self):
        return "Stop And Wait"

    def send_file(self, origin: socket.socket, file: io.BufferedReader):
        seq = 0
        while chunk := file.read(MAX_PAYLOAD_SIZE):
            while True:
                origin.send(pickle.dumps(Segment(seq_num=seq, payload=chunk)))
                try:
                    reply = self._recv_segment(origin)

                    # llega retrasmisión.
                    if reply.flags["SYN"]:
                        origin.send(pickle.dumps(
                            Segment(ack_flag=True, seq_num=1, ack_num=1)))
                        continue

                    if reply.flags["ACK"] and reply.ack_num == seq:
                        seq = 1 - seq
                        break
                except socket.timeout:
                    continue

        self._teardown_sender(origin, seq)

    def recv_file(self, origin: socket.socket, file: io.BufferedReader):
        expected_seq = 0
        while True:
            segment = self._recv_segment(origin)

            # parche por si el último ACK del Handshake se pierde
            if segment.flags["SYN"]:
                origin.send(pickle.dumps(
                    Segment(ack_flag=True, ack_num=1, seq_num=1)))
                continue

            if segment.seq_num != expected_seq:
                origin.send(pickle.dumps(
                    Segment(ack_flag=True, ack_num=1-expected_seq)))
                continue

            if segment.flags["FIN"]:
                self._teardown_recv(origin, expected_seq)
                break

            file.write(segment.payload)
            origin.send(pickle.dumps(
                Segment(ack_flag=True, ack_num=expected_seq)))
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

    def send_file(self, sock: socket.socket, file: io.BufferedReader):
        window_size = 10
        base = 0
        next_seq_num = 0

        chunks = []
        while True:
            data = file.read(MAX_PAYLOAD_SIZE)
            if not data:
                break
            chunks.append(data)

        total_packets = len(chunks)
        sock.setblocking(False)

        while base < total_packets:
            while next_seq_num < base + window_size and \
                    next_seq_num < total_packets:
                packet = Segment(seq_num=next_seq_num,
                                 payload=chunks[next_seq_num])
                sock.send(pickle.dumps(packet))
                if base == next_seq_num:
                    start_time = time.time()
                next_seq_num += 1

            current_time = time.time()
            time_left = max(0.0, TIMEOUT -
                            (current_time - start_time))
            ready, _, _ = select.select([sock], [], [], time_left)

            if ready:
                try:
                    ack_packet: Segment = self._recv_segment(sock)
                    start_time = time.time()

                    if ack_packet.flags["SYN"]:
                        sock.send(pickle.dumps(
                            Segment(ack_flag=True, seq_num=1, ack_num=1)))
                        continue

                    if ack_packet.flags["ACK"] and ack_packet.ack_num >= base:
                        base = ack_packet.ack_num + 1
                except Exception:
                    pass
            else:
                next_seq_num = base

        sock.setblocking(True)
        self._teardown_sender(sock, base)

    def recv_file(self, sock: socket.socket, file: io.BufferedWriter):
        expected_seq_num = 0

        while True:
            try:
                sock.settimeout(None)
                segment: Segment = self._recv_segment(sock)

                # parche por si el último ACK del Handshake se pierde
                if segment.flags["SYN"]:
                    sock.send(pickle.dumps(
                        Segment(ack_flag=True, seq_num=1, ack_num=1)))
                    continue

                if segment.flags["FIN"] and \
                        segment.seq_num == expected_seq_num:
                    break

                if segment.seq_num == expected_seq_num:
                    file.write(segment.payload)
                    sock.send(pickle.dumps(
                        Segment(ack_flag=True, ack_num=expected_seq_num)))
                    expected_seq_num += 1
                else:
                    sock.send(pickle.dumps(
                        Segment(ack_flag=True, ack_num=expected_seq_num - 1)))
            except Exception:
                continue

        self._teardown_recv(sock, expected_seq_num)

    def client_send(self, origin: socket.socket, dest: tuple[str, int],
                    file: io.BufferedReader, filename: str):
        self._handshake(origin, dest, OP_UPLOAD, filename)
        self.send_file(origin, file)

    def client_recv(self, dest: socket.socket, origin: tuple[str, int],
                    file: io.BufferedReader, filename: str):
        self._handshake(dest, origin, OP_DOWNLOAD, filename)
        self.recv_file(dest, file)
