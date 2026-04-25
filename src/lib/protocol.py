from lib.segment import Segment, MTU
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


class StopAndWait(Protocol):
    ID = "stop-and-wait"

    def __repr__(self):
        return "Stop And Wait"

    def send_file(self, origin_socket: socket.socket, file):
        while (chunk := file.read(MAX_PAYLOAD_SIZE)):
            while True:
                origin_socket.send(pickle.dumps(Segment(payload=chunk)))

                bytes_received = bytearray(MTU)
                q_bytes_received = origin_socket.recv_into(bytes_received)
                reply = pickle.loads(bytes_received[:q_bytes_received])
                if reply.flags["ACK"] is True:
                    break

        origin_socket.send(pickle.dumps(Segment(fin_flag=True)))


class GoBackN(Protocol):
    ID = "go-back-n"

    def __repr__(self):
        return "Go Back N"
