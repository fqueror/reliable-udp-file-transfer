from lib.settings import OP_UPLOAD, OP_DOWNLOAD, HIGH_VERBOSITY
from lib.protocol.protocol import Protocol, MAX_PAYLOAD_SIZE
from lib.segment import Segment, SYN, ACK, FIN
import pickle
import socket
import io

STOP_AND_WAIT_ID = "stop-and-wait"

class StopAndWait(Protocol):
    ID = STOP_AND_WAIT_ID

    def __repr__(self):
        return "Stop And Wait"

    def send_file(self, origin: socket.socket, file: io.BufferedReader):
        seq = 0

        self.log(f"SENDER: Starting transfer with {self}.")

        while chunk := file.read(MAX_PAYLOAD_SIZE):
            while True:
                origin.send(pickle.dumps(Segment(seq_num=seq, payload=chunk)))
                self.log(f"SENDER: Sent packet {seq}", HIGH_VERBOSITY)

                try:
                    reply = self._recv_segment(origin)

                    # llega retrasmisión.
                    if reply.flags[SYN]:
                        origin.send(pickle.dumps(
                            Segment(ack_flag=True, seq_num=1, ack_num=1)))
                        continue

                    if reply.flags[ACK] and reply.ack_num == seq:
                        self.log(f"SENDER: Received ACK {seq}", HIGH_VERBOSITY)
                        seq = 1 - seq
                        break
                except socket.timeout:
                    self.log(f"SENDER: Timeout! Resending packet {seq}",
                             HIGH_VERBOSITY)
                    continue

        self._teardown_sender(origin, seq)

    def recv_file(self, origin: socket.socket, file: io.BufferedReader):
        expected_seq = 0

        self.log(f"RECEIVER: Ready to receive data with {self}.")

        retries = 0
        while retries < 8:
            try:
                segment = self._recv_segment(origin)
            except socket.timeout:
                retries += 1
                self.log("RECEIVER: Timeout! Resending SYN.", HIGH_VERBOSITY)
                continue

            if segment.flags[SYN]:
                origin.send(pickle.dumps(
                    Segment(ack_flag=True, ack_num=1, seq_num=1)))
                continue

            if segment.seq_num != expected_seq:
                self.log("RECEIVER: Wrong sequence number. Expected " + \
                         f"{expected_seq}, got {segment.seq_num}",
                         HIGH_VERBOSITY)
                origin.send(pickle.dumps(
                    Segment(ack_flag=True, ack_num=1 - expected_seq)))
                continue

            if segment.flags[FIN]:
                self.log("RECEIVER: FIN received.")
                self._teardown_recv(origin, expected_seq)
                break

            file.write(segment.payload)
            self.log(f"RECEIVER: Got packet {expected_seq}", HIGH_VERBOSITY)
            retries = 0
            origin.send(pickle.dumps(
                Segment(ack_flag=True, ack_num=expected_seq)))
            expected_seq = 1 - expected_seq

        if retries >= 8:
            self.log("RECEIVER: Timeout! Resending FIN.", HIGH_VERBOSITY)
            raise TimeoutError("Timeout while receiving file.")

    def client_send(self, origin: socket.socket, dest: tuple[str, int],
                    file: io.BufferedReader, filename: str):
        self._handshake(origin, dest, OP_UPLOAD, filename)
        self.send_file(origin, file)

    def client_recv(self, dest: socket.socket, origin: tuple[str, int],
                    file: io.BufferedReader, filename: str):
        self._handshake(dest, origin, OP_DOWNLOAD, filename)
        self.recv_file(dest, file)
