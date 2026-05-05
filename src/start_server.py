from lib.parser import get_args
from lib.server import Server
from lib.settings import START_SERVER

if __name__ == "__main__":
    args = get_args(START_SERVER)

    server = Server(args)
    server.start()
