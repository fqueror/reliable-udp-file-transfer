import socket
import pickle
import threading
import queue

# We use the MTU (Maximum Transmission Unit) as our segment's maximum size so
# as to avoid fragmentation in lower Internet layers.
MTU = 1500

class Server:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 12000
        self.socket = None
        self.storage = "./server_storage/"
        # Lista de clientes activos. Cada cliente tiene su cola
        self.active_transfers = {}

    def config_server(self, args):
        self.host = args.host
        self.port = args.port


    def handle_client(self, client_addr, segment, client_queue):
        print(f"[NUEVO HILO] Atendiendo a {client_addr}")

        #if paquete es upload{}
        filepath = "" #Filepath que da el segmento
        with open(filepath, "wb") as file:
            file.write(segment.payload)

            while True:
                segment = client_queue.get()
                if segment.flags["FIN"]:
                    print(f"[FINALIZADO] Transferencia completa para {client_addr}")
                    break

                file.write(segment.payload)

        del self.active_transfers[client_addr]

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

                thread = threading.Thread(target=self.handle_client, args=(addr, segment, client_queue))
                thread.start()

            else:
                self.active_transfers[addr].put(segment)


            if segment.flags["FIN"]:
                break
            file.write(segment.payload)

        self.socket.close()
        file.close()
