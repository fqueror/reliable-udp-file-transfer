# Operation
OP_UPLOAD = "UPLOAD"
OP_DOWNLOAD = "DOWNLOAD"
DOWNLOAD = "download"
UPLOAD = "upload"
START_SERVER = "start-server"

# Protocol
MTU = 5000
MAX_PAYLOAD_SIZE = 4500
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
