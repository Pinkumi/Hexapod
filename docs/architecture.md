# Arquitectura

Fase 1 separa panel estático (`frontend`) del servicio FastAPI (`backend/app`). `SimRobot` es el único dueño del estado y solo produce valores claramente marcados como simulación. La telemetría se publica por `/ws/telemetry`; `/ws/control` admite solicitud de parada. Las rutas REST validan comandos con Pydantic. El servidor reinicia siempre desarmado. No se ha creado controlador físico.

Futuras capas: adaptador hardware, arbitraje de movimiento, sensores, cámara compartida con buffer acotado, inferencia desacoplada, API y presentación. Solo una capa de movimiento deberá arbitrar comandos y prioridades de seguridad.
