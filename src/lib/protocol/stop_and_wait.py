import io
import pickle
import socket
import time

from lib.protocol.protocol import Protocol, TimeoutVariable
from lib.segment import Segment
from lib.settings import MAX_PAYLOAD_SIZE, OP_UPLOAD, OP_DOWNLOAD


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
                        self.log(
                            f"SENDER: Received ACK {seq}",
                            is_verbose=True)
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
                self.log(
                    f"RECEIVER: Wrong sequence number. Expected {expected_seq}, got {
                        segment.seq_num}", is_verbose=True)
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
