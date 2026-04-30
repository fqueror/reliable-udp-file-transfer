from lib.metadata import Metadata
import queue
from lib.segment import Segment
import socket
import pickle
import os
from lib.constants import MTU, MAX_PAYLOAD_SIZE, OP_DOWNLOAD, OP_UPLOAD

# An MSS is the Maximum Segment Size, though it defines the maximum payload
# size. According to Kurose's book, 1460 bytes is its typical value.
# TODO Since we use `Segment`, our header is larger than 40 bytes, and we then
# TODO must use an MSS lower than the typical. However, we should use the
# TODO highest possible one within that range. For now, 1400 does the
# TODO job, but we must check if it is the best possible value.


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

    # Called by the server to receive a file from a client.
    def upload_file(self, server_socket, client_addr, client_queue, storage, filename):
        filepath = os.path.join(storage, str(filename))
        file = open(filepath, "wb")
        ack = pickle.dumps(Segment(ack_flag=True))
        expected_seq = 0

        while True:
            try:
                segment = client_queue.get(timeout=5)
            except queue.Empty:
                print("[SERVER] Timeout, abortando")
                file.close()
                return

            if segment.flags["FIN"]:
                server_socket.sendto(pickle.dumps(Segment(ack_flag=True, fin_flag=True)), client_addr)
                break

            if segment.seq_num == expected_seq:
                file.write(segment.payload)
                expected_seq = 1 - expected_seq  

            server_socket.sendto(ack, client_addr)

        print(f"[FIN] {filename} recibido")
        file.close()
        print(f"[SERVER] Archivo guardado: {os.path.getsize(filepath)} bytes")

    # Called by the server to send a file to a client.
    def download_file(
        self, server_socket, client_addr, client_queue, storage, filename
    ):
        filepath = os.path.join(storage, str(filename))
        file = open(filepath, "rb")

        while chunk := file.read(MAX_PAYLOAD_SIZE):
            while True:
                server_socket.sendto(
                    pickle.dumps(
                        Segment(
                            payload=chunk)),
                    client_addr)

                reply = client_queue.get()

                if reply.flags["ACK"] is True:
                    break

        server_socket.sendto(pickle.dumps(Segment(fin_flag=True)), client_addr)
        file.close()
        print(f"[FIN] {filename} enviado")

    # Called by the client to send a file to the server.
    def send_file(self, origin_socket: socket.socket, file, filename):
        origin_socket.settimeout(0.5)

        metadata = Metadata(filename=filename, protocol=self.ID, operation=OP_UPLOAD)
        first_segment = Segment(payload=pickle.dumps(metadata))

        while True:
            origin_socket.send(pickle.dumps(first_segment))
            try:
                bytes_received = bytearray(MTU)
                q_bytes_received = origin_socket.recv_into(bytes_received)
                reply = pickle.loads(bytes_received[:q_bytes_received])
                if reply.flags["ACK"] is True:
                    break
            except socket.timeout:
                continue

        seq = 0
        chunk = file.read(MAX_PAYLOAD_SIZE)
        chunk_num = 0

        while chunk:
            segment = Segment(payload=chunk, seq_num=seq)
            chunk_num += 1
            #print(f"[CLIENT] Enviando chunk #{chunk_num}")
            while True:
                origin_socket.send(pickle.dumps(segment))
                try:
                    bytes_received = bytearray(MTU)
                    q_bytes_received = origin_socket.recv_into(bytes_received)
                    reply = pickle.loads(bytes_received[:q_bytes_received])
                    if reply.flags["ACK"] is True:
                        seq = 1 - seq
                        #print(f"[CLIENT] ACK #{chunk_num} recibido")  
                        break
                except socket.timeout:
                    #print(f"[CLIENT] Timeout chunk #{chunk_num}, reintentando...")
                    continue

            chunk = file.read(MAX_PAYLOAD_SIZE)

        while True:
            origin_socket.send(pickle.dumps(Segment(fin_flag=True)))
            try:
                bytes_received = bytearray(MTU)
                q_bytes_received = origin_socket.recv_into(bytes_received)
                reply = pickle.loads(bytes_received[:q_bytes_received])
                if reply.flags["ACK"] is True:
                    break
            except socket.timeout:
                continue

        print("[CLIENT] FIN enviado y confirmado, transferencia completa")

    # Called by the client to download a file from the server.
    def receive_file(self, client_socket: socket.socket, file, filename):
        client_socket.settimeout(0.5)

        metadata = Metadata(filename=filename,
                            protocol=self.ID, operation=OP_DOWNLOAD)
        client_socket.send(
            pickle.dumps(
                Segment(
                    payload=pickle.dumps(metadata))))

        while True:
            try:
                bytes_received = bytearray(MTU)
                q_bytes_received = client_socket.recv_into(bytes_received)
                reply = pickle.loads(bytes_received[:q_bytes_received])

                if reply.flags["FIN"] is True:
                    break

                file.write(reply.payload)
                client_socket.send(pickle.dumps(Segment(ack_flag=True)))
            except socket.timeout:
                continue

        return


class GoBackN(Protocol):
    ID = "go-back-n"

    def __repr__(self):
        return "Go Back N"
