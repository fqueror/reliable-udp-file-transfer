import socket
CHUNK_SIZE = 1024


class UdpClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addr = (self.host, self.port)

    def upload(self, source_path):
        socket_client = self.sock
        print(f"Iniciando subida del archivo: {source_path}")
        with open(source_path, 'rb') as f:

            # abro el archivo en modo lectura binaria
            while True:

                chunk = f.read(CHUNK_SIZE)

                # separo el arhivo en chunks de 1024 bytes
                if not chunk:
                    break
                socket_client.sendto(chunk, self.addr)

        print("Envío finalizado.")
        socket_client.close()
