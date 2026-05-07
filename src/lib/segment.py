SYN = "SYN"
ACK = "ACK"
FIN = "FIN"

class Segment:
    """
    We use a Python class to construct the segment because it is easier to
    manage than bytes directly, plus we know we can convert them into and from
    bytes by using [`pickle`](
    https://realpython.com/python-bytes/#serialize-python-objects-using-a-binary-format).

    The disadvantage is that we must use a lower MSS, since our segment's
    header is larger than 40 bytes.
    """

    def __init__(self, seq_num: int = 0, ack_num: int = 0,
                 syn_flag: bool = False, ack_flag: bool = False,
                 fin_flag: bool = False, payload: bytes = b""):
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.flags = {SYN: syn_flag, ACK: ack_flag, FIN: fin_flag}
        self.payload = payload
