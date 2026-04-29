from lib.metadata import Metadata, OP_UPLOAD, OP_DOWNLOAD
from lib.segment import Segment
import socket
import pickle
import io


# We use the MTU (Maximum Transmission Unit) as our segment's maximum size so
# as to avoid fragmentation in lower Internet layers.
MTU = 1500
# An MSS is the Maximum Segment Size, though it defines the maximum payload
# size. According to Kurose's book, 1460 bytes is its typical value.
# TODO Since we use `Segment`, our header is larger than 40 bytes, and we then
# TODO must use an MSS lower than the typical. However, we should use the
# TODO highest possible one within that range. For now, 1400 does the
# TODO job, but we must check if it is the best possible value.
MAX_PAYLOAD_SIZE = 1400


class Protocol:
    @classmethod
    def from_str(cls, str):
        for subclass in cls.__subclasses__():
            if str == subclass.ID:
                return subclass()

    def recv(self, dest: socket.socket) -> Segment:
        """
        If `dest` is already connected to an `origin` socket with [`connect`](
        https://docs.python.org/3/library/socket.html#socket.socket.connect),
        you can use this method to get a segment received from `origin`.
        """

        bytes_received = bytearray(MTU)
        q_bytes_received = dest.recv_into(bytes_received)
        return pickle.loads(bytes_received[:q_bytes_received])


class StopAndWait(Protocol):
    ID = "stop-and-wait"

    def __repr__(self):
        return "Stop And Wait"

    def server_recv(self, file: io.BufferedReader, origin: socket.socket):
        origin.send(pickle.dumps(Segment(ack_flag=True)))

        while True:
            segment = self.recv(origin)

            if segment.flags["FIN"]:
                break

            file.write(segment.payload)
            origin.send(pickle.dumps(Segment(ack_flag=True)))

    def server_send(self, origin: socket.socket, file: io.BufferedReader):
        origin.send(pickle.dumps(Segment(ack_flag=True)))

        while chunk := file.read(MAX_PAYLOAD_SIZE):
            while True:
                origin.send(pickle.dumps(Segment(payload=chunk)))

                if self.recv(origin).flags["ACK"] is True:
                    break

        origin.send(pickle.dumps(Segment(fin_flag=True)))

    def client_send(self, origin: socket.socket, dest: tuple[str, int],
                    file: io.BufferedReader, filename: str):
        while True:
            origin.sendto(pickle.dumps(
                Segment(payload=pickle.dumps(
                    Metadata(OP_UPLOAD, filename, self.ID)))), dest)

            bytes_received = bytearray(MTU)
            q_bytes_received, dest = origin.recvfrom_into(bytes_received)
            origin.connect(dest)
            if pickle.loads(bytes_received[:q_bytes_received]
                            ).flags["ACK"] is True:
                break

        while chunk := file.read(MAX_PAYLOAD_SIZE):
            while True:
                origin.send(pickle.dumps(Segment(payload=chunk)))

                if self.recv(origin).flags["ACK"] is True:
                    break

        origin.send(pickle.dumps(Segment(fin_flag=True)))

    def client_recv(self, dest: socket.socket, origin: tuple[str, int],
                    file: io.BufferedReader, filename: str):
        while True:
            dest.sendto(pickle.dumps(
                Segment(payload=pickle.dumps(
                    Metadata(OP_DOWNLOAD, filename, self.ID)))), origin)
            bytes_received = bytearray(MTU)
            q_bytes_received, origin = dest.recvfrom_into(bytes_received)
            dest.connect(origin)

            if pickle.loads(bytes_received[:q_bytes_received]
                            ).flags["ACK"] is True:
                break

        while True:
            reply = self.recv(dest)

            if reply.flags["FIN"] is True:
                break

            file.write(reply.payload)
            dest.send(pickle.dumps(Segment(ack_flag=True)))


class GoBackN(Protocol):
    ID = "go-back-n"

    def __repr__(self):
        return "Go Back N"
