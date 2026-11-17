# Hardware y auditoría

Entorno: Raspberry Pi OS Lite/Debian 13, ARM64, Python 3.13.5. `rpicam-hello --list-cameras`: no cameras available. No nodos I²C/GPIO visibles en esta sesión. No se comprobó presencia física de shield, dirección I²C, sensor CSI, nivel Echo, revisión de LEDs ni alimentación. La sesión no permite inferir conexiones por el mapeo de referencia proporcionado.

Fuentes de referencia: [documentación oficial FNK0052](https://docs.freenove.com/projects/fnk0052/en/latest/) y [repositorio oficial](https://github.com/Freenove/Freenove_Big_Hexapod_Robot_Kit_for_Raspberry_Pi). El repositorio declara licencia CC BY-NC-SA 3.0; este proyecto no copia código. Su historial indica diferencias de drivers/LED por versiones de Raspberry Pi y placa de conexión; verificar versión antes de implementar.
