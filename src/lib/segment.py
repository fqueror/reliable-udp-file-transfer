class Segment:
    """
    We use a Python class to construct the segment because it is easier to
    manage than bytes directly, plus we know we can convert them into and from
    bytes by using [`pickle`](
    https://realpython.com/python-bytes/#serialize-python-objects-using-a-binary-format).

    The disadvantage is that we must use a lower MSS, since our segment's
    header is larger than 40 bytes.
    """

    def __init__(self, ack_flag: bool = False, fin_flag: bool = False,
                 payload: bytes = b""):
        self.flags = {"ACK": ack_flag, "FIN": fin_flag}
        self.payload = payload
