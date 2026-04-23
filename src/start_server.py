from lib.parser import get_args
import socket


if __name__ == "__main__":
    args = get_args("start-server")

    print("ARRANCO EL SERVIDOR")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', 12000))

    archivo_data_recibida = open("archivo_recibido.txt", "wb")

    data, addr = server_socket.recvfrom(1024)
    archivo_data_recibida.write(data)
    print(f"Received data from {addr}: {data.decode()}")

    server_socket.close()
    archivo_data_recibida.close()
