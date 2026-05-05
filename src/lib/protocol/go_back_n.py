import socket
import io
import time
import pickle
import select

from lib.protocol.protocol import Protocol, TimeoutVariable
from lib.settings import MAX_PAYLOAD_SIZE, OP_UPLOAD, OP_DOWNLOAD
from lib.segment import Segment


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

        self.log(
            f"SENDER: Starting transfer of {total_packets} packets with Go-Back-N.")

        while base < total_packets:
            while next_seq_num < base + window_size and \
                    next_seq_num < total_packets:
                packet = Segment(seq_num=next_seq_num,
                                 payload=chunks[next_seq_num])
                sock.send(pickle.dumps(packet))
                self.log(
                    f"SENDER: Sent packet {next_seq_num}",
                    is_verbose=True)
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
                        self.log(
                            f"SENDER: Received ACK {
                                ack_packet.ack_num}",
                            is_verbose=True)
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

                if segment.flags["ERR"]:
                    sock.send(pickle.dumps(Segment(ack_flag=True)))
                    raise ConnectionError(pickle.loads(segment.payload))

                if segment.flags["FIN"] and \
                        segment.seq_num == expected_seq_num:
                    break

                if segment.seq_num == expected_seq_num:
                    file.write(segment.payload)
                    self.log(
                        f"RECEIVER: Got packet {expected_seq_num}",
                        is_verbose=True)
                    sock.send(pickle.dumps(
                        Segment(ack_flag=True, ack_num=expected_seq_num)))
                    expected_seq_num += 1
                else:
                    self.log(
                        f"RECEIVER: Out of order. Expected {expected_seq_num}, got {
                            segment.seq_num}", is_verbose=True)
                    sock.send(pickle.dumps(
                        Segment(ack_flag=True, ack_num=expected_seq_num - 1)))
            except ConnectionError as e:
                print(f"Connection error: {e}")
                return
            except Exception as e:
                print(f"Error: {e}")
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
