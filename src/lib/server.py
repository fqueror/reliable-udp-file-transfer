import socket
import pickle
import threading
import queue
import os

from lib.segment import Segment

# We use the MTU (Maximum Transmission Unit) as our segment's maximum size so
# as to avoid fragmentation in lower Internet layers.
MTU = 1500
OP_UPLOAD = "UPLOAD"
OP_DOWNLOAD = "DOWNLOAD"
MAX_PAYLOAD_SIZE = 1400

class Server:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 12000
        self.socket = None
        self.storage = ""
        # Lista de clientes activos. Cada cliente tiene su cola
        self.active_transfers = {}

    def config_server(self, args):
        self.host = args.host
        self.port = args.port
        self.storage = args.storage
        os.makedirs(self.storage, exist_ok=True)


    def upload_file(self, client_addr, client_queue, first_segment):
        filename = first_segment.filename
        filepath = os.path.join(self.storage, str(filename))
        file = open(filepath, "wb")

        file.write(first_segment.payload)
        ack = pickle.dumps(Segment(ack_flag=True))
        self.socket.sendto(ack, client_addr)

        while True:
            segment = client_queue.get()

            if segment.flags["FIN"]:
                del self.active_transfers[client_addr]
                break

            file.write(segment.payload)

            self.socket.sendto(ack, client_addr)

        print(f"[FIN] {filename} recibido")
        file.close()

    def download_file(self, client_addr, client_queue, first_segment):
        filename = first_segment.filename
        filepath = os.path.join(self.storage, str(filename))
        file = open(filepath, "rb")

        ack = pickle.dumps(Segment(ack_flag=True))

        while chunk := file.read(MAX_PAYLOAD_SIZE):
            while True:
                self.socket.sendto(pickle.dumps(
                    Segment(payload=chunk)), client_addr)

                self.socket.sendto(ack, client_addr)
                reply = client_queue.get()

                if reply.flags["ACK"] is True:
                    break

        self.socket.sendto(pickle.dumps(Segment(fin_flag=True)), client_addr)
        file.close()
        print(f"[FIN] {filename} enviado")

    def handle_client(self, client_addr, client_queue):
        print(f"[NUEVO HILO] Atendiendo a {client_addr}")
        segment = client_queue.get()

        if segment.operation == OP_UPLOAD:
            self.upload_file(client_addr, client_queue, segment)

        elif segment.operation == OP_DOWNLOAD:
            self.download_file(client_addr, client_queue, segment)



    def start_server(self):
        print(f"ARRANCO EL SERVIDOR en {self.host}:{self.port}")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))

        try:
            while True:
                data, addr = self.socket.recvfrom(MTU*2)
                segment = pickle.loads(data)

                if addr not in self.active_transfers:
                    client_queue = queue.Queue()
                    self.active_transfers[addr] = client_queue
                    client_queue.put(segment)
                    thread = threading.Thread(target=self.handle_client, args=(addr, client_queue))
                    thread.daemon = True
                    thread.start()

                else:
                    self.active_transfers[addr].put(segment)
        except KeyboardInterrupt:
            self.socket.close()
            print("\n[APAGANDO] Cerrando el servidor de forma segura...")



