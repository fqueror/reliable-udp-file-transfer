# Uso de mininet

Dentro de la carpeta download es donde se guardan los archivos que sean descargados mediante esta herramienta. Tambien se adjunta una imagen de ejemplo para que se pueda probar sin tener que importar o descargar nada.

## Instalacion

- **Herramienta mininet:**
```bash
sudo apt-get install mininet
```

- **Controlador para el switch:**
```bash
sudo apt-get install openvswitch-testcontroller
```

## Levantar la red

```bash
sudo python3 mininet/mininet_topology.py
```

Esto crea los host conectados al switch

## Comandos de uso

### Levantar servidor

**Formato:**
```bash
h2 python3 src/start_server.py -H <IP> -p <PORT> -s <STORAGE_DIR> &
```

**Ejemplo:**
```bash
h2 python3 src/start_server.py -H 10.0.0.2 -p 8080 -s ./storage &
```

### Upload

**Formato:**
```bash
h1 python3 src/upload.py -H <IP> -p <PORT> -s <FILEPATH> -n <FILENAME> -r <PROTOCOL>
```

**Ejemplo:**
```bash
h1 python3 src/upload.py -H 10.0.0.2 -p 8080 -s mininet/foto1.jpg -n archivo.jpg -r stop-and-wait
```

### Download

**Formato:**
```bash
h1 python3 src/download.py -H <IP> -p <PORT> -d <DEST_DIR> -n <FILENAME> -r <PROTOCOL>
```

**Ejemplo:**
```bash
h1 python3 src/download.py -H 10.0.0.2 -p 8080 -d mininet/download -n archivo.jpg -r stop-and-wait
```

### Protocolos de uso

Stop & Wait: stop-and-wait

Go-Back-N: go-back-n

## Verificaciones

### Packet loss analisis

```bash
h1 ping -c 1000 -i 0.01 10.0.0.2
```

### Ver procesos corriendo

```bash
h2 ps aux | grep python3
```

### Bajar servidor

```bash
h2 pkill -f python3
```

## Limpiar mininet

```bash
exit
sudo mn -c
```

## Eliminar archivos creados en mininet

sudo rm "<FILEPATH>"