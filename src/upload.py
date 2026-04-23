from lib.parser import get_args
from lib.UdpClient import UdpClient


if __name__ == "__main__":
    args = get_args("upload")

    client = UdpClient(args["host"], args["port"])
    client.upload(args["src"])
