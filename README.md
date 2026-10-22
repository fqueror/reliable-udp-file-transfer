# Reliable UDP File Transfer

Client-server file transfer over UDP in Python, with two reliable data transfer protocols implemented from scratch: **Stop-and-Wait** and **Go-Back-N**.

Assignment for Computer Networks (TA048) at the Faculty of Engineering, University of Buenos Aires (FIUBA), first semester of 2026.

## Features

- Upload and download files between a client and a server.
- Stop-and-Wait or Go-Back-N (window size 10), selected per transfer.
- Sequence numbers, cumulative ACKs, timeouts and retransmissions.
- Connection setup with a three-way handshake and teardown with FIN/ACK.
- Multithreaded server: each client is handled on its own thread and socket.
- Mininet topology with 10% packet loss for testing.

## Requirements

- Python 3.9+ (standard library only)
- [Mininet](https://mininet.org/), only to run the test topology

## Usage

Run the commands from the repository root.

```bash
# Start the server
python3 src/start_server.py -H 0.0.0.0 -p 12000 -s storage

# Upload sample.jpg and store it on the server as photo.jpg
python3 src/upload.py -H 127.0.0.1 -p 12000 -s sample.jpg -n photo.jpg -r go-back-n

# Download photo.jpg into the downloads/ directory
python3 src/download.py -H 127.0.0.1 -p 12000 -n photo.jpg -d downloads -r stop-and-wait
```

| Option | Description |
| --- | --- |
| `-H`, `--host` | Server IP address |
| `-p`, `--port` | Server port |
| `-s`, `--src` | Upload: source file. Server: storage directory (default `storage`) |
| `-n`, `--name` | File name on the server |
| `-d`, `--dst` | Download: destination directory (default: current directory) |
| `-r`, `--protocol` | `stop-and-wait` or `go-back-n` |
| `-v`, `-q` | Verbose or quiet output |

The client needs `-H`, `-p`, `-n` and `-r`.

## Testing with Mininet

`mininet/topology.py` creates one switch, a server and four clients. The server link drops 10% of packets, so both data segments and ACKs are lost.

```bash
sudo python3 mininet/topology.py
mininet> xterm server client1 client2
```

Then start the server on `10.0.0.5`, run transfers from the clients and compare the files with `md5sum`. Use `sudo mn -c` to clean up leftover topologies.

## Results

Transfer time for a 5 MB file, measured with `time`:

| Protocol | Operation | 0% loss | 10% loss |
| --- | --- | --- | --- |
| Stop-and-Wait | Upload | 0.57 s | 47.7 s |
| Stop-and-Wait | Download | 0.86 s | 49.1 s |
| Go-Back-N | Upload | 0.34 s | 22.3 s |
| Go-Back-N | Download | 0.39 s | 23.3 s |

With 10% loss, Go-Back-N achieved about twice the throughput of Stop-and-Wait. The 10 MB and 15 MB tests gave the same ratio.

## Design notes

- Segments are Python objects serialized with `pickle`. The payload is capped at 1350 bytes so each datagram fits in a 1500-byte MTU without fragmentation.
- The retransmission timeout is fixed at 50 ms. An adaptive RTT-based timeout was tested and performed worse in this environment.
- Corrupted datagrams are discarded by the UDP checksum, so segments carry no checksum of their own.

## Project structure

```
src/
├── start_server.py, upload.py, download.py   # entry points
└── lib/
    ├── server.py                             # multithreaded server
    ├── segment.py                            # segment format
    └── protocol/
        ├── protocol.py                       # handshake and teardown
        ├── stop_and_wait.py
        └── go_back_n.py
mininet/topology.py                           # test topology
```
