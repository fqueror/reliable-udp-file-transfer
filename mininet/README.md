# 🌐 MiniNet

Instalamos MiniNet y el controlador para el _switch_ con:

```bash
sudo apt install mininet openvswitch-testcontroller
```

Levantamos la red con:

```bash
sudo python3 mininet/mininet_topology.py
```

---

Ahí, nos encontraremos en la **CLI** de MiniNet. Desde acá, podremos ejecutar comandos en cada _host_: en cada línea de comandos, indicamos el _host_ y luego el programa a ejecutar. Por ejemplo…

- Levantamos el servidor: `server python3 src/start_server.py -H 10.0.0.2 -p 12000 -s cloud &`.
- Subimos un archivo: `client python3 src/upload.py -H 10.0.0.2 -p 12000 -s mininet/foto1.jpg -n archivo.jpg -r stop-and-wait`.

---

En cuanto a **análisis**, tenemos:

- Si indicamos **`time`** entre el _host_ y el programa, nos mostraría durante cuánto tiempo se ejecutó el comando. Por ejemplo, si usamos `client time python3 src/upload.py -H 10.0.0.2 -p 12000 -s mininet/foto1.jpg -n archivo.jpg -r stop-and-wait`, obtendríamos cuánto tardó en subirse el archivo.
- Con `server ping -c 1000 -i 0.01 10.0.0.2` obtenemos un **análisis de pérdida de paquetes**.
- Con `server ps aux | grep python3` vemos los procesos Python corriendo.

---

Para cerrar el servidor, una posibilidad es: `server pkill -f python3`.

Y para limpiar MiniNet, primero debemos salir de la CLI con `exit` y luego ejecutar `sudo mn -c`.
