from lib.parser import get_args
from lib.server import Server

if __name__ == "__main__":
    args = get_args("start-server")

    server = Server()
    server.config_server(args)
    server.start_server()
