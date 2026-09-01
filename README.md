# Reliable File Transfer Application over UDP (`custom-file-transfer-protocol`)

A client-server application built in Python that implements custom reliable data transfer protocols (**Stop-and-Wait** 
and **Go-Back-N**) over unreliable networks. Includes automated scripts for packet loss and latency performance 
evaluation using **Mininet**.

---

## 🚀 Key Features

- **Custom Transport Protocols:** Implements **Stop-and-Wait (ARQ)** and **Go-Back-N (GBN)** window-based mechanisms 
- over UDP.
- **Concurrent File Sharing:** Client-server architecture supporting simultaneous file uploads and downloads across 
- multiple concurrent clients.
- **Integrity Verification:** Automated checksum validations using `MD5` hashes to verify data integrity post-transfer.
- **Performance Analysis Tools:** Scripted execution measuring end-to-end latency, execution time, and throughput under 
- simulated packet loss scenarios.

---

## 🛠️ Concepts Applied

- **Reliable Data Transfer (RDT):** Sequence numbering, timeouts, cumulative ACKs, and retransmissions over UDP.
- **Flow Control:** Sliding window mechanisms (Go-Back-N).
- **Network Emulation:** Multi-host topologies and traffic simulation in Mininet.

---

## 💻 Tech Stack

- **Language:** Python 3
- **Network Virtualization:** Mininet, Open vSwitch (OVS)
- **System Analysis:** `xterm`, `md5sum`, `time`, `ping`

---

## 🏃 Usage & Execution

### 1. Launch Network Topology

```bash
sudo python3 mininet/topology.py
```

### 2. Start the Server

Inside the Mininet environment (or via xterm server):

```Bash
python3 src/start_server.py -H 10.0.0.5 -p 12000 -s cloud
```

### 3. Upload & Download Files

Upload using Go-Back-N:

```Bash
python3 src/upload.py -H 10.0.0.5 -p 12000 -s sample.jpg -n Uploaded.jpg -r go-back-n
```

Download using Stop-and-Wait:

```Bash
python3 src/download.py -H 10.0.0.5 -p 12000 -n Uploaded.jpg -d Downloaded.jpg -r stop-and-wait
```

---

## 👥 Multi-Client Testing (Demo)

You can spin up multiple terminal instances inside Mininet using `xterm` to test concurrent uploads and downloads over
**Stop-and-Wait** and **Go-Back-N**:

**Launch Mininet with xterm instances:**

   ```bash
   sudo python3 mininet/topology.py
   xterm server client1 client2 client3 client4
   ```
   
1. Start Server (in server xterm):

```Bash
python3 src/start_server.py -H 10.0.0.5 -p 12000 -s cloud
```

2. Simultaneous File Transfers (across client terminals):

Client 1 (Upload SAW): 
```bash
python3 src/upload.py -H 10.0.0.5 -p 12000 -s file.jpg -n UploadedSAW.jpg -r stop-and-wait
```

Client 2 (Upload GBN): 
```bash
python3 src/upload.py -H 10.0.0.5 -p 12000 -s file.jpg -n UploadedGBN.jpg -r go-back-n
```

Client 3 (Download SAW): 
```bash
python3 src/download.py -H 10.0.0.5 -p 12000 -n Existing.jpg -d DownloadedSAW -r stop-and-wait
```

Client 4 (Download GBN): 
```bash
python3 src/download.py -H 10.0.0.5 -p 12000 -n Existing.jpg -d DownloadedGBN -r go-back-n
```

## 📈 Performance & Network Analysis
Benchmarking Execution Time: Prepend time to measure end-to-end transfer latency across protocols.

Packet Loss Simulation: Run ICMP ping sweeps to evaluate packet loss rates on specific links:

```Bash
client ping -c 1000 -i 0.01 10.0.0.5
```

Process Monitoring: Inspect running python instances on the server host:

```Bash
server ps aux | grep python3
```

## 🧹 Environment Cleanup & Troubleshooting

If the server hangs or you need to terminate all running Python instances across Mininet hosts, execute:

```bash
server pkill -f python3
```

To clean up stale Mininet topologies and free up open ports:

```Bash
sudo mn -c
```
