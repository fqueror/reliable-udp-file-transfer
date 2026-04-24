import socket
import pickle

class Server:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 12000
        self.socket = None
        # We use the MTU (Maximum Transmission Unit) as our segment's maximum size so
        # as to avoid fragmentation in lower Internet layers.
        self.MTU = 1500

    def config_server(self, args):
        self.host = args.host
        self.port = args.port

    def start_server(self):
        print("ARRANCO EL SERVIDOR")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))

        # Change the file's extension to match the one being received:
        file = open("archivo_recibido.mp4", "wb")

        while True:
            bytes_received = bytearray(self.MTU)
            q_bytes_received = self.socket.recv_into(bytes_received)
            segment = pickle.loads(bytes_received[:q_bytes_received])

            if segment.flags["FIN"]:
                break
            file.write(segment.payload)

        self.socket.close()
        file.close()
