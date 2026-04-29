OP_UPLOAD = "UPLOAD"
OP_DOWNLOAD = "DOWNLOAD"


class Metadata:
    def __init__(self, operation, filename, protocol):
        self.operation = operation
        self.filename = filename
        self.protocol = protocol
