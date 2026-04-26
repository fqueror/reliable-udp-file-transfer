import socket
import pickle
import threading
import queue
import os

from lib.segment import Segment

# We use the MTU (Maximum Transmission Unit) as our segment's maximum size so
# as to avoid fragmentation in lower Internet layers.
MTU = 1500

class Server:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 12000
        self.socket = None
        self.storage = ""
        # Lista de clientes activos. Cada cliente tiene su cola
        self.active_transfers = {}
        self.file = None

    def config_server(self, args):
        self.host = args.host
        self.port = args.port
        self.storage = args.storage
        os.makedirs(self.storage, exist_ok=True)
        # Change the file's extension to match the one being received:
        file = open(args.storage + "/archivo_recibido.mp4", "wb")
        self.file = file


    def handle_client(self, client_addr, client_queue):
        print(f"[NUEVO HILO] Atendiendo a {client_addr}")
        #if paquete es upload{}

        self.socket.sendto(pickle.dumps(Segment(ack_flag=True)), client_addr)
        ack = pickle.dumps(Segment(ack_flag=True))

        while True:
            segment = client_queue.get()

            if segment.flags["FIN"]:
                print(f"[FINALIZADO] Transferencia completa para {client_addr}")
                del self.active_transfers[client_addr]

            self.file.write(segment.payload)

            self.socket.sendto(ack, client_addr)



        #elif paquete es download{}


    def start_server(self):
        print(f"ARRANCO EL SERVIDOR en {self.host}:{self.port}")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))

        while True:
            data, addr = self.socket.recvfrom(MTU)
            segment = pickle.loads(data)

            if addr not in self.active_transfers:
                client_queue = queue.Queue()
                self.active_transfers[addr] = client_queue
                client_queue.put(segment)
                thread = threading.Thread(target=self.handle_client, args=(addr, client_queue))
                thread.start()

            else:
                self.active_transfers[addr].put(segment)


