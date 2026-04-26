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
OP_DOWNLOAD = "DOWNLOAD"
OP_UPLOAD = "UPLOAD"


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

    def send_file(self, origin_socket: socket.socket, file, filename):
        while chunk := file.read(MAX_PAYLOAD_SIZE):
            while True:
                origin_socket.send(pickle.dumps(
                    Segment(payload=chunk, operation=OP_UPLOAD, filename=filename)))

                bytes_received = bytearray(MTU * 2)
                q_bytes_received = origin_socket.recv_into(bytes_received)
                reply = pickle.loads(bytes_received[:q_bytes_received])
                if reply.flags["ACK"] is True:
                    break

        origin_socket.send(pickle.dumps(Segment(fin_flag=True)))

    def receive_file(self, client_socket: socket.socket, file, filename):
        client_socket.send(pickle.dumps(Segment(operation=OP_DOWNLOAD, filename=filename)))

        while True:
            bytes_received = bytearray(MTU * 2)  # Pickle necesita > 1500
            q_bytes_received = client_socket.recv_into(bytes_received)
            reply = pickle.loads(bytes_received[:q_bytes_received])

            if reply.flags["FIN"] is True:
                break

            file.write(reply.payload)
            client_socket.send(pickle.dumps(Segment(ack_flag=True)))

        return


class GoBackN(Protocol):
    ID = "go-back-n"

    def __repr__(self):
        return "Go Back N"
