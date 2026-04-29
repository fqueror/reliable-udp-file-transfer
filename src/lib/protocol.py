from lib.constants import MTU, OP_DOWNLOAD, OP_UPLOAD
from lib.metadata import Metadata
from lib.segment import Segment
import socket
import pickle

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

    def recv_segment(self, socket: socket.socket):
        bytes_received = bytearray(MTU)
        q_bytes_received = socket.recv_into(bytes_received)
        return pickle.loads(bytes_received[:q_bytes_received])


class StopAndWait(Protocol):
    ID = "stop-and-wait"

    def __repr__(self):
        return "Stop And Wait"

    def server_recv(self, file, server_socket, client_addr, client_queue):
        server_socket.sendto(pickle.dumps(Segment(ack_flag=True)), client_addr)

        while True:
            segment = client_queue.get()

            if segment.flags["FIN"]:
                break

            file.write(segment.payload)
            server_socket.sendto(pickle.dumps(Segment(ack_flag=True)),
                                 client_addr)

    def server_send(self, origin_socket, client_addr, client_queue, file):
        while chunk := file.read(MAX_PAYLOAD_SIZE):
            while True:
                origin_socket.sendto(pickle.dumps(Segment(payload=chunk)),
                                     client_addr)

                if client_queue.get().flags["ACK"] is True:
                    break

        origin_socket.sendto(pickle.dumps(Segment(fin_flag=True)), client_addr)

    def client_send(self, origin_socket: socket.socket, file, filename):
        while True:
            origin_socket.send(pickle.dumps(
                Segment(payload=pickle.dumps(
                    Metadata(OP_UPLOAD, filename, self.ID)))))

            if self.recv_segment(origin_socket).flags["ACK"] is True:
                break

        while chunk := file.read(MAX_PAYLOAD_SIZE):
            while True:
                origin_socket.send(pickle.dumps(Segment(payload=chunk)))

                if self.recv_segment(origin_socket).flags["ACK"] is True:
                    break

        origin_socket.send(pickle.dumps(Segment(fin_flag=True)))

    def client_recv(self, client_socket: socket.socket, file, filename):
        client_socket.send(pickle.dumps(
            Segment(payload=pickle.dumps(
                Metadata(OP_DOWNLOAD, filename, self.ID)))))

        while True:
            reply = self.recv_segment(client_socket)

            if reply.flags["FIN"] is True:
                break

            file.write(reply.payload)
            client_socket.send(pickle.dumps(Segment(ack_flag=True)))


class GoBackN(Protocol):
    ID = "go-back-n"

    def __repr__(self):
        return "Go Back N"
