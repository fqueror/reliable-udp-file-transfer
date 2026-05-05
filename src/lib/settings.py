# Operation
OP_UPLOAD = "UPLOAD"
OP_DOWNLOAD = "DOWNLOAD"
DOWNLOAD = "download"
UPLOAD = "upload"
START_SERVER = "start-server"

# Protocol
# We use the MTU (Maximum Transmission Unit) as our segment's maximum size so
# as to avoid fragmentation in lower Internet layers.
MTU = 1500
# An MSS is the Maximum Segment Size, though it defines the maximum payload
# size. According to Kurose's book, 1460 bytes is its typical value.
# TODO Since we use `Segment`, our header is larger than 40 bytes, and we then
# TODO must use an MSS lower than the typical. However, we should use the
# TODO highest possible one within that range. For now, 1300 does the job, but
# TODO we must check if it is the best possible value.
MAX_PAYLOAD_SIZE = 1350
MAX_TIMEOUT_HANDSHAKE = 10
STOP_AND_WAIT = "stop-and-wait"
GO_BACK_N = "go-back-n"
WINDOW_SIZE = 10

# Server
MAX_ATTEMPTS = 3
SERVER_DEFAULT_HOST = "0.0.0.0"
SERVER_DEFAULT_PORT = 12000
SERVER_DEFAULT_STORAGE = "./storage"

# File
FILE_WRITER = "wb"
FILE_READER = "rb"

# Error
FILE_NOT_FOUND = "File not found"
PERMISSION_DENIED = "Permission denied"
FILE_PATH_NOT_SPECIFIED = "File path not specified"
DIRECTORY_NOT_FOUND = "Directory not found"

# Flags
ACK = "ACK"
FIN = "FIN"
ERR = "ERR"

# Timeout
SRTT = 0.05
RTTVAR = 0.01
RTO = 0.1
ALPHA = 0.125
BETA = 0.25
SEC_TIMEOUT_LIMIT = 60
