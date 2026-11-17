"""Captura CSI compartida. La cámara es opcional y jamás bloquea el servidor."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any

@dataclass
class CameraSettings:
    width: int = 640
    height: int = 480
    quality: int = 75
    rotation: int = 0

class CameraService:
    """Una instancia Picamera2 y un único worker; consumidores leen el último JPEG."""
    def __init__(self) -> None:
        self.settings = CameraSettings()
        self._camera: Any = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.Condition()
        self._jpeg: bytes | None = None
        self._error: str | None = None
        self._frames = 0
        self._fps = 0.0
        self._started = False
        self._lifecycle = threading.RLock()

    def status(self) -> dict:
        return {"enabled": self._started, "available": self._started and self._error is None,
                "fps": round(self._fps, 1), "resolution": [self.settings.width, self.settings.height],
                "quality": self.settings.quality, "error": self._error, "hardware": "CSI"}

    def start(self) -> dict:
        with self._lifecycle:
            if self._started: return self.status()
            try:
                from picamera2 import Picamera2
                cam = Picamera2()
                cfg = cam.create_video_configuration(main={"size": (self.settings.width, self.settings.height), "format": "RGB888"}, buffer_count=4)
                cam.configure(cfg)
                cam.start()
                self._camera, self._error, self._started = cam, None, True
                self._jpeg = None
                self._stop.clear()
                self._thread = threading.Thread(target=self._capture, name="hexavision-camera", daemon=True)
                self._thread.start()
            except Exception as exc:
                self._error = f"{type(exc).__name__}: {exc}"
                self._camera = None
                self._started = False
            return self.status()

    def _capture(self) -> None:
        try:
            import cv2
            import numpy as np
            marks: list[float] = []
            while not self._stop.is_set():
                frame = self._camera.capture_array()
                if self.settings.rotation:
                    frame = np.rot90(frame, k=(self.settings.rotation // 90) % 4).copy()
                ok, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, self.settings.quality])
                if not ok: continue
                now = time.monotonic(); marks.append(now); marks = marks[-30:]
                self._fps = (len(marks)-1)/(marks[-1]-marks[0]) if len(marks)>1 and marks[-1]>marks[0] else 0
                with self._lock:
                    self._jpeg = encoded.tobytes(); self._frames += 1; self._lock.notify_all()
        except Exception as exc:
            self._error = f"Captura fallida: {type(exc).__name__}: {exc}"
            with self._lock: self._lock.notify_all()

    def latest(self, after_frame: int = 0, timeout: float = 2.0) -> tuple[int, bytes] | None:
        with self._lock:
            if self._frames <= after_frame:
                self._lock.wait_for(lambda: self._frames > after_frame or not self._started, timeout)
            if self._jpeg is None or self._frames <= after_frame: return None
            return self._frames, self._jpeg

    def configure(self, width: int, height: int, quality: int, rotation: int) -> dict:
        if (width, height) not in ((640,480),(1296,972),(1920,1080)): raise ValueError("Resolución no permitida")
        if rotation not in (0, 90, 180, 270): raise ValueError("Rotación debe ser 0/90/180/270")
        with self._lifecycle:
            self.settings = CameraSettings(width, height, max(30,min(95,quality)),rotation)
            if self._started:
                self.stop(); return self.start()
            return self.status()

    def stop(self) -> dict:
        with self._lifecycle:
            self._stop.set()
            if self._thread and self._thread.is_alive(): self._thread.join(timeout=3)
            self._thread = None
            if self._camera is not None:
                try: self._camera.stop(); self._camera.close()
                except Exception as exc: self._error = f"Cierre fallido: {exc}"
            self._camera = None; self._started = False
            with self._lock: self._jpeg = None; self._lock.notify_all()
            return self.status()

camera = CameraService()
