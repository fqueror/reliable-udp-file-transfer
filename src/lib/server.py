import socket

class Server:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 12000
        self.socket = None

    def start_server(self):
        print("ARRANCO EL SERVIDOR")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))

        archivo_data_recibida = open("archivo_recibido.txt", "wb")

        while True:
            data, addr = self.socket.recvfrom(1024)
            archivo_data_recibida.write(data)

            print(f"Received data from {addr}: {data.decode()}")

        server_socket.close()
        archivo_data_recibida.close()