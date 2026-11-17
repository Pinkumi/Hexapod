"""Servidor HexaVision. Solo simulación; no controla GPIO ni servos."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from .camera import camera

ROOT = Path(__file__).resolve().parents[2]

class RobotMode(StrEnum):
    DISARMED = "DISARMED"
    IDLE = "IDLE"
    MANUAL = "MANUAL"
    AUTONOMOUS = "AUTONOMOUS"
    CALIBRATION = "CALIBRATION"
    FAULT = "FAULT"
    EMERGENCY_STOP = "EMERGENCY_STOP"

class Command(BaseModel):
    direction: Literal["forward", "back", "left", "right", "turn_left", "turn_right", "stop"]
    speed: float = Field(default=0, ge=0, le=1)

class ModeRequest(BaseModel):
    mode: Literal["MANUAL", "IDLE", "AUTONOMOUS"]

class SimRobot:
    def __init__(self):
        self.mode = RobotMode.DISARMED
        self.armed = False
        self.emergency = False
        self.command = Command(direction="stop")
        self.started = datetime.now(timezone.utc)
    def state(self):
        return {"mode": self.mode, "armed": self.armed, "emergency_stop": self.emergency,
                "command": self.command.model_dump(), "hardware": "SIMULATED",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "sensors": {"ultrasonic_cm": None, "imu": None, "battery_v": None},
                "camera": camera.status(), "vision": {"enabled": False, "fps": 0, "hardware": "INACTIVA"}}

robot = SimRobot()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Arranca desarmado siempre. No se inicializa hardware real.
    robot.mode = RobotMode.DISARMED
    robot.armed = False
    yield
    await run_in_threadpool(camera.stop)

app = FastAPI(title="HexaVision", version="0.1.0", lifespan=lifespan)

@app.get("/")
async def index(): return FileResponse(ROOT / "frontend/index.html")

@app.get("/api/health")
async def health(): return {"ok": True, "hardware": "SIMULATED", "mode": robot.mode}

@app.get("/api/system")
@app.get("/api/robot/state")
async def state(): return robot.state()

@app.get("/api/sensors")
async def sensors(): return robot.state()["sensors"]

@app.get("/api/camera/status")
async def camera_status(): return camera.status()

@app.post("/api/camera/start")
async def camera_start(): return await run_in_threadpool(camera.start)

@app.post("/api/camera/stop")
async def camera_stop(): return await run_in_threadpool(camera.stop)

class CameraConfig(BaseModel):
    width: int = 640
    height: int = 480
    quality: int = Field(default=75, ge=30, le=95)
    rotation: Literal[0, 90, 180, 270] = 0

@app.post("/api/camera/settings")
async def camera_settings(req: CameraConfig):
    try: return await run_in_threadpool(camera.configure, req.width, req.height, req.quality, req.rotation)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc

@app.get("/stream.mjpg")
async def mjpeg():
    async def frames():
        last_frame = 0
        while True:
            result = await run_in_threadpool(camera.latest, last_frame, 2.0)
            if not camera.status()["available"]: break
            if result is None:
                await asyncio.sleep(.15); continue
            last_frame, frame = result
            yield b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(frame)).encode() + b"\r\n\r\n" + frame + b"\r\n"
    if not camera.status()["available"]: raise HTTPException(503, "Cámara apagada o no disponible")
    return StreamingResponse(frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.post("/api/robot/arm")
async def arm():
    if robot.emergency: raise HTTPException(409, "Libera la parada de emergencia antes de armar")
    robot.armed, robot.mode = True, RobotMode.IDLE
    return robot.state()

@app.post("/api/robot/disarm")
async def disarm():
    robot.command = Command(direction="stop"); robot.armed = False; robot.mode = RobotMode.DISARMED
    return robot.state()

@app.post("/api/robot/stop")
async def stop():
    robot.command = Command(direction="stop"); robot.armed = False
    robot.emergency = True; robot.mode = RobotMode.EMERGENCY_STOP
    return robot.state()

@app.post("/api/robot/reset-stop")
async def reset_stop():
    robot.emergency = False; robot.mode = RobotMode.DISARMED; robot.armed = False
    return robot.state()

@app.post("/api/robot/mode")
async def set_mode(req: ModeRequest):
    if req.mode != "IDLE" and not robot.armed: raise HTTPException(409, "Sistema desarmado")
    robot.command = Command(direction="stop") # cancela marcha previa al cambiar de modo
    robot.mode = RobotMode(req.mode)
    return robot.state()

@app.post("/api/robot/command")
async def command(req: Command):
    if robot.emergency or not robot.armed or robot.mode != RobotMode.MANUAL:
        raise HTTPException(409, "Comando rechazado: requiere armado y modo MANUAL")
    robot.command = req
    return robot.state()

@app.websocket("/ws/telemetry")
async def telemetry(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.send_json(robot.state())
            await asyncio.sleep(1)
    except WebSocketDisconnect: pass

@app.websocket("/ws/control")
async def control(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_json()
            if data.get("type") == "stop":
                robot.command = Command(direction="stop")
            await ws.send_json({"ok": True, "state": robot.state()})
    except WebSocketDisconnect: pass
