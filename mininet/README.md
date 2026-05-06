# 🌐 MiniNet

Instalamos MiniNet y el controlador para el _switch_ con:

```bash
sudo apt install -y mininet openvswitch-testcontroller
```

Levantamos la red con:

```bash
sudo python3 mininet/mininet_topology.py
```

---

Ahí, nos encontraremos en la **CLI** de MiniNet. Desde acá, podremos ejecutar comandos en cada _host_: en cada línea de comandos, indicamos el _host_ y luego el programa a ejecutar. Por ejemplo…

- Levantamos el servidor: `server python3 src/start_server.py -H 10.0.0.3 -p 12000 -s cloud &`. Dado que agregamos el `&` para que el servidor se ejecute en el _background_ y así poder ejecutar luego los clientes, para poder ver su _output_, podemos agregar `> server.log 2>&1` antes del `&`.
- Subimos un archivo: `client1 python3 src/upload.py -H 10.0.0.3 -p 12000 -s mininet/foto1.jpg -n archivo.jpg -r stop-and-wait`.
- Descargar un archivo: `client1 python3 src/download.py -H 10.0.0.3 -p 12000 -n archivo.jpg -r stop-and-wait`.

Si queremos probar el funcionamiento de **varios clientes con un único servidor**, podemos (habiendo primero ya iniciado el servidor) hacer `client1 python3 src/upload.py -H 10.0.0.3 -p 12000 -s test_file.bin -n UploadedBy1.bin -r stop-and-wait &` e inmediantamente después (mientras ese archivo se sigue subiendo) `client2 python3 src/upload.py -H 10.0.0.3 -p 12000 -s test_file.bin -n UploadedBy2.bin -r stop-and-wait`.

---

En cuanto a **análisis**, tenemos:

- Si indicamos **`time`** entre el _host_ y el programa, nos mostraría durante cuánto tiempo se ejecutó el comando. Por ejemplo, si usamos `client time python3 src/upload.py -H 10.0.0.3 -p 12000 -s mininet/foto1.jpg -n archivo.jpg -r stop-and-wait`, obtendríamos cuánto tardó en subirse el archivo.
- Con `client ping -c 1000 -i 0.01 10.0.0.3` obtenemos un **análisis de pérdida de paquetes**.
- Con `server ps aux | grep python3` vemos los procesos Python corriendo.

---

Para cerrar el servidor, una posibilidad es: `server pkill -f python3`.

Y para limpiar MiniNet, primero debemos salir de la CLI con `exit` y luego ejecutar `sudo mn -c`.
