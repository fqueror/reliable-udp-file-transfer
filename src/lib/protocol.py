from lib.metadata import Metadata, OP_UPLOAD, OP_DOWNLOAD
from lib.segment import Segment
import socket
import pickle
import io
import time
import select

MTU = 5000
MAX_PAYLOAD_SIZE = 4500
MAX_TIMEOUT_HANDSHAKE = 10


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
                self.log(f"Intento {attempt + 1}/{MAX_TIMEOUT_HANDSHAKE} fallido. Reintentando...")

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


class StopAndWait(Protocol):
    ID = "stop-and-wait"

    def __repr__(self):
        return "Stop And Wait"

    def send_file(self, origin: socket.socket, file: io.BufferedReader):
        timeout_var = TimeoutVariable()
        origin.settimeout(timeout_var.rto)
        seq = 0

        self.log("SENDER: Starting transfer with Stop & Wait.")

        while chunk := file.read(MAX_PAYLOAD_SIZE):
            while True:
                origin.send(pickle.dumps(Segment(seq_num=seq, payload=chunk)))
                self.log(f"SENDER: Sent packet {seq}", is_verbose=True)

                try:
                    t_inicio = time.time()
                    reply = self._recv_segment(origin)

                    if reply.flags["ACK"] and reply.ack_num == seq:
                        self.log(f"SENDER: Received ACK {seq}", is_verbose=True)
                        rtt_muestra = time.time() - t_inicio
                        origin.settimeout(timeout_var.update(rtt_muestra))
                        seq = 1 - seq
                        break
                except socket.timeout:
                    self.log(f"SENDER: Timeout! Resending packet {seq}")
                    origin.settimeout(timeout_var.on_timeout())
                    continue

        self._teardown_sender(origin, seq, timeout_var)

    def recv_file(self, origin: socket.socket, file: io.BufferedReader):
        timeout_var = TimeoutVariable()
        origin.settimeout(timeout_var.rto)
        expected_seq = 0

        self.log("RECEIVER: Ready to receive data with Stop & Wait.")

        while True:
            try:
                segment = self._recv_segment(origin)
            except socket.timeout:
                origin.settimeout(timeout_var.on_timeout())
                continue

            if segment.seq_num != expected_seq:
                self.log(f"RECEIVER: Wrong sequence number. Expected {expected_seq}, got {segment.seq_num}",
                         is_verbose=True)
                origin.send(pickle.dumps(
                    Segment(ack_flag=True, ack_num=1 - expected_seq)))
                continue

            if segment.flags["ERR"]:
                origin.send(pickle.dumps(Segment(ack_flag=True)))
                raise ConnectionError(pickle.loads(segment.payload))

            if segment.flags["FIN"]:
                self.log("RECEIVER: FIN received.")
                self._teardown_recv(origin, expected_seq, timeout_var)
                break

            file.write(segment.payload)
            self.log(f"RECEIVER: Got packet {expected_seq}", is_verbose=True)
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
        timeout_manager = TimeoutVariable()
        start_time = time.time()

        self.log(f"SENDER: Starting transfer of {total_packets} packets with Go-Back-N.")

        while base < total_packets:
            while next_seq_num < base + window_size and \
                    next_seq_num < total_packets:
                packet = Segment(seq_num=next_seq_num,
                                 payload=chunks[next_seq_num])
                sock.send(pickle.dumps(packet))
                self.log(f"SENDER: Sent packet {next_seq_num}", is_verbose=True)
                if base == next_seq_num:
                    start_time = time.time()
                next_seq_num += 1

            current_time = time.time()
            time_left = max(0.0, timeout_manager.rto -
                            (current_time - start_time))
            ready, _, _ = select.select([sock], [], [], time_left)

            if ready:
                try:
                    ack_packet: Segment = self._recv_segment(sock)
                    if ack_packet.flags["ACK"] and ack_packet.ack_num >= base:
                        self.log(f"SENDER: Received ACK {ack_packet.ack_num}", is_verbose=True)
                        sample_rtt = time.time() - start_time
                        timeout_manager.update(sample_rtt)
                        base = ack_packet.ack_num + 1
                        start_time = time.time()
                except Exception:
                    pass
            else:
                self.log(f"SENDER: Timeout! Resending from {base}")
                next_seq_num = base
                start_time = time.time()

        sock.setblocking(True)
        sock.settimeout(timeout_manager.rto)
        self._teardown_sender(sock, base, timeout_manager)

    def recv_file(self, sock: socket.socket, file: io.BufferedWriter):
        expected_seq_num = 0
        timeout_manager = TimeoutVariable()
        self.log("RECEIVER: Ready to receive data with Go-Back-N.")

        while True:
            try:
                sock.settimeout(None)
                segment: Segment = self._recv_segment(sock)

                if segment.flags["FIN"] and \
                        segment.seq_num == expected_seq_num:
                    break

                if segment.seq_num == expected_seq_num:
                    file.write(segment.payload)
                    self.log(f"RECEIVER: Got packet {expected_seq_num}", is_verbose=True)
                    sock.send(pickle.dumps(
                        Segment(ack_flag=True, ack_num=expected_seq_num)))
                    expected_seq_num += 1
                else:
                    self.log(f"RECEIVER: Out of order. Expected {expected_seq_num}, got {segment.seq_num}",
                             is_verbose=True)
                    sock.send(pickle.dumps(
                        Segment(ack_flag=True, ack_num=expected_seq_num - 1)))
            except Exception:
                continue

        self._teardown_recv(sock, expected_seq_num, timeout_manager)

    def client_send(self, origin: socket.socket, dest: tuple[str, int],
                    file: io.BufferedReader, filename: str):
        self._handshake(origin, dest, OP_UPLOAD, filename)
        self.send_file(origin, file)

    def client_recv(self, dest: socket.socket, origin: tuple[str, int],
                    file: io.BufferedReader, filename: str):
        self._handshake(dest, origin, OP_DOWNLOAD, filename)
        self.recv_file(dest, file)


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
