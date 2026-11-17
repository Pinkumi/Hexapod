# HexaVision

Base web para el hexápodo. La versión actual opera **solo en simulación**; ningún código activa GPIO, I²C o servos.

## Entorno auditado

Debian GNU/Linux 13 (Trixie), ARM64, kernel Raspberry Pi `6.18.60+rpt`, Python 3.13.5. Está disponible `rpicam-hello`, pero no detectó cámara (`No cameras available`). En esta sesión no se ven dispositivos `/dev/i2c*` ni `/dev/gpiochip*`; por tanto, I²C/GPIO no se verificaron y no se intentó habilitarlos. FastAPI/Uvicorn/Pydantic/Picamera2 no están instalados; OpenCV sí. `vcgencmd` no pudo acceder a `/dev/vcio`. No se ejecutaron instaladores del fabricante ni se modificaron pines o alimentación.

## Ejecutar

```sh
cd ~/hexapod
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```

Abrir `http://pinkupi.local:8000`. La API escucha en la red local y aún no tiene autenticación: usar solo en una red confiable. No configurar reenvío de puertos.

## Estructura

- `backend/app`: API, estado simulado y WebSockets.
- `frontend`: panel web estático.
- `docs`: auditoría, arquitectura, seguridad y plan de fases.
- `config`: parámetros explícitos para futura integración, sin calibración física asumida.

Estados de seguridad inician en `DISARMED`. La parada de emergencia simula enclavamiento; nunca sustituye el corte físico de potencia. Antes de integrar hardware serán necesarios drivers separados seleccionados por configuración y revisión física de conexiones/alimentación.
