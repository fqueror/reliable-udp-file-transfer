from lib.protocol.protocol import Protocol, MAX_PAYLOAD_SIZE, TIMEOUT
from lib.settings import OP_UPLOAD, OP_DOWNLOAD, HIGH_VERBOSITY
from lib.segment import Segment, SYN, ACK, FIN, ERR
import socket
import pickle
import select
import time
import io

GO_BACK_N_ID = "go-back-n"

class GoBackN(Protocol):
    ID = GO_BACK_N_ID

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

        self.log(f"SENDER: Starting transfer of {total_packets} packets with " \
                 + f"{self}.")

        while base < total_packets:
            while next_seq_num < base + window_size and \
                    next_seq_num < total_packets:
                packet = Segment(seq_num=next_seq_num,
                                 payload=chunks[next_seq_num])
                sock.send(pickle.dumps(packet))
                self.log(f"SENDER: Sent packet {next_seq_num}", HIGH_VERBOSITY)
                if base == next_seq_num:
                    start_time = time.time()
                next_seq_num += 1

            current_time = time.time()
            time_left = max(0.0, TIMEOUT - (current_time - start_time))
            ready, _, _ = select.select([sock], [], [], time_left)

            if ready:
                try:
                    ack_packet: Segment = self._recv_segment(sock)
                    start_time = time.time()

                    if ack_packet.flags[SYN]:
                        sock.send(pickle.dumps(
                            Segment(ack_flag=True, seq_num=1, ack_num=1)))
                        continue

                    if ack_packet.flags[ACK] and ack_packet.ack_num >= base:
                        self.log(f"SENDER: Received ACK {ack_packet.ack_num}",
                                 HIGH_VERBOSITY)
                        base = ack_packet.ack_num + 1
                except Exception:
                    pass
            else:
                self.log(f"SENDER: Timeout! Resending from {base}",
                         HIGH_VERBOSITY)
                next_seq_num = base

        sock.setblocking(True)
        self._teardown_sender(sock, base)

    def recv_file(self, sock: socket.socket, file: io.BufferedWriter):
        expected_seq_num = 0
        self.log(f"RECEIVER: Ready to receive data with {self}.")

        while True:
            try:
                sock.settimeout(None)
                segment: Segment = self._recv_segment(sock)

                # parche por si el último ACK del Handshake se pierde
                if segment.flags[SYN]:
                    sock.send(pickle.dumps(
                        Segment(ack_flag=True, seq_num=1, ack_num=1)))
                    continue

                if segment.flags[ERR]:
                    sock.send(pickle.dumps(Segment(ack_flag=True)))
                    raise ConnectionError(pickle.loads(segment.payload))

                if segment.flags[FIN] and \
                        segment.seq_num == expected_seq_num:
                    break

                if segment.seq_num == expected_seq_num:
                    file.write(segment.payload)
                    self.log(f"RECEIVER: Got packet {expected_seq_num}",
                             HIGH_VERBOSITY)
                    sock.send(pickle.dumps(
                        Segment(ack_flag=True, ack_num=expected_seq_num)))
                    expected_seq_num += 1
                else:
                    self.log("RECEIVER: Out of order. Expected " + \
                             f"{expected_seq_num}, got {segment.seq_num}",
                             HIGH_VERBOSITY)
                    sock.send(pickle.dumps(
                        Segment(ack_flag=True, ack_num=expected_seq_num - 1)))
            except ConnectionError as e:
                raise e
            except Exception as e:
                print(f"Error: {e}")
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
