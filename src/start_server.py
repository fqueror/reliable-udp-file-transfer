from lib.parser import get_args
from lib.segment import Segment, MTU
import socket
import pickle
import os

from lib.server import Server

if __name__ == "__main__":
    args = get_args("start-server")

    server = Server()
    server.config_server(args)
    server.start_server()


    #while True:
        # TODO Una vez tengamos el _3-way-handshake_, vamos a poder usar
        # TODO `socket.connect` para evitar tener que obtener el `client_addr`
        # TODO cada vez. O con los _threads_.
        #bytes_received = bytearray(MTU)
        #q_bytes_received, client_addr = socket.recvfrom_into(bytes_received)
        #segment = pickle.loads(bytes_received[:q_bytes_received])
        #file.write(segment.payload)

        #socket.sendto(pickle.dumps(Segment(ack_flag=True)), client_addr)

        #if segment.flags["FIN"]:
           # break

    #socket.close()
    #file.close()
