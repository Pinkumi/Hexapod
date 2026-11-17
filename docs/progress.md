# Progreso

## Fase 0

- Confirmados Debian 13, ARM64 y Python 3.13.5.
- rpicam disponible, pero sin cámara detectada en esta sesión.
- Sin nodos I²C/GPIO visibles; sensores/shield no auditables desde aquí.
- No se modificó hardware ni se corrió instalador de Freenove.

## Fase 1

- API FastAPI, estado simulado, controles de armado/desarmado, modos, comandos, E-stop y WebSockets implementados.
- Panel responsive con marca de simulación y lecturas ausentes como `—`.
- Pendiente instalar dependencias y comprobar servidor en navegador.
- Sin pruebas ejecutadas todavía.

## Fase 2 en implementación

- Añadidos servicio central de Picamera2, estado, endpoints de inicio/apagado/configuración y stream MJPEG compartido.
- El panel incluye controles para cámara, tamaño/calidad y FPS. IA sigue apagada de forma independiente.
- `app.openapi()` registra GET `/api/camera/status`, POST `/api/camera/start`, POST `/api/camera/stop` y GET `/stream.mjpg`; `/ws/telemetry` sigue presente. Los 404 observados corresponden a una instancia que no cargó el `main.py` actual; reiniciar Uvicorn recarga las rutas.
- Mejorado el stream para entregar cada frame nuevo una sola vez y terminar si la captura falla. La resolución valida pares exactos admitidos.
- Verificación de esta sesión: Picamera2 no está instalado por `apt`; `rpicam-hello` informó “No cameras available” y no hay nodos de vídeo visibles. No se pudo capturar imagen real ni medir FPS.
- `py_compile` pasa. No se pudieron hacer requests HTTP de socket porque el sandbox bloquea sockets locales; TestClient requiere `httpx2`, ausente. Los handlers verifican una respuesta controlada con error cuando Picamera2 no está disponible.
- IA: no se incluyó un modelo ni pesos. Evitamos producir detecciones ficticias. Próximo paso: fijar modelo ARM64/Python 3.13 y adquirir explícitamente sus pesos, luego inferencia desacoplada.
