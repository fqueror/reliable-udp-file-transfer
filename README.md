# 🌐 TP1 _File Transfer_

## 👋🏼 Preparación

Instalamos MiniNet y el controlador para el _switch_ con:

```bash
sudo apt install -y mininet openvswitch-testcontroller
```

Levantamos la red con:

```bash
sudo python3 mininet/topology.py
```

Indicando el nombre del archivo en `of` y la cantidad de MBs en `count`, podemos generar archivos de prueba con: `dd if=/dev/urandom of=OG.bin bs=1M count=5`. Luego, para chequear la integridad de los archivos enviados/recibidos, podemos ver el _checksum_ de cada uno con `md5sum`.

## 🧰 Uso

### ℹ️ General

Ahí, nos encontraremos en la **CLI** de MiniNet. Desde acá, podremos ejecutar comandos en cada _host_: en cada línea de comandos, indicamos el _host_ y luego el programa a ejecutar. Por ejemplo…

- Levantamos el servidor: `server python3 src/start_server.py -H 10.0.0.5 -p 12000 -s cloud &`. Dado que agregamos el `&` para que el servidor se ejecute en el _background_ y así poder ejecutar luego los clientes, para poder ver su _output_, podemos agregar `> server.log 2>&1` antes del `&`.
- Subimos un archivo: `client1 python3 src/upload.py -H 10.0.0.5 -p 12000 -s OG.jpg -n Uploaded.jpg -r go-back-n`.
- Descargar un archivo: `client1 python3 src/download.py -H 10.0.0.5 -p 12000 -n Uploaded.jpg -r go-back-n`.

### 👥 Varios _hosts_

Si queremos probar el funcionamiento de **varios clientes con un único servidor**, podemos iniciar varias terminales usando `xterm` dentro de la CLI de MiniNet. Por ejemplo, para crear una terminal para `server` y otra para `client1`, hacemos: `xterm server client1`.

## 👨🏼‍🏫 Demostración

Los siguientes son los pasos para poder a mostrar a los profesores el uso de la aplicación para 2 subidas y 2 descargas, todo en simultáneo y usando ambos protocolos.

Empezamos con:

```bash
sudo python3 mininet/topology.py
xterm server client1 client2 client3 client4
```

Luego, en la terminal del servidor: `python3 src/start_server.py -H 10.0.0.5 -p 12000 -s cloud`. En alguna otra, subimos `OG.jpg` como `AlreadyUploaded.jpg` haciendo `python3 src/upload.py -H 10.0.0.5 -p 12000 -s OG.jpg -n AlreadyUploaded.jpg -r go-back-n`. Con esto, ya tenemos todo preparado.

Finalmente, ejecutamos cada uno de estos comandos en cada una de las terminales creadas (podes pasar por cada una pegando los comandos y luego volver a pasar por cada una ejecutándolos apretando `Enter`):

1. `time python3 src/upload.py -H 10.0.0.5 -p 12000 -s OG.jpg -n UploadedWithSAW.jpg -r stop-and-wait`
1. `time python3 src/upload.py -H 10.0.0.5 -p 12000 -s OG.jpg -n UploadedWithGBN.jpg -r go-back-n`
1. `time python3 src/download.py -H 10.0.0.5 -p 12000 -n AlreadyUploaded.jpg -d DownloadedWithSAW -r stop-and-wait`
1. `time python3 src/download.py -H 10.0.0.5 -p 12000 -n AlreadyUploaded.jpg -d DownloadedWithGBN -r go-back-n`

## 📈 Análisis

En cuanto a **análisis**, tenemos:

- Si indicamos **`time`** entre el _host_ y el programa, nos mostraría durante cuánto tiempo se ejecutó el comando. Por ejemplo, si usamos `client time python3 src/upload.py -H 10.0.0.5 -p 12000 -s OG.jpg -n Uploaded.jpg -r stop-and-wait`, obtendríamos cuánto tardó en subirse el archivo.
- Con `client ping -c 1000 -i 0.01 10.0.0.5` obtenemos un **análisis de pérdida de paquetes**.
- Con `server ps aux | grep python3` vemos los procesos Python corriendo.

## 👋🏼 Cierre

Para cerrar el servidor, una posibilidad es: `server pkill -f python3`.

Y para limpiar MiniNet, primero debemos salir de la CLI con `exit` y luego ejecutar `sudo mn -c`.
