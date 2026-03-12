"""
GawdBotE — FastAPI Backend
REST + WebSocket API for the web dashboard and all interfaces.
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import settings
from agents.orchestrator import Orchestrator
from memory.supabase import SupabaseMemory
from memory.local import LocalMemory

# ---- Logging ----
logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
log = logging.getLogger("gawdbote")

# ---- Memory backend ----
memory = (
    SupabaseMemory(settings.supabase_url, settings.supabase_anon_key)
    if settings.supabase_url and settings.supabase_anon_key
    else LocalMemory(settings.sqlite_path)
)

# ---- Orchestrator ----
orchestrator = Orchestrator(memory=memory, settings=settings)

# ---- WebSocket connection manager ----
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, data: dict):
        for ws in self.active:
            await ws.send_json(data)

manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    log.info("GawdBotE starting up...")
    await memory.initialize()
    log.info(f"Memory backend: {type(memory).__name__}")
    log.info(f"LLM: {settings.claude_smart_model}")
    log.info(f"Backend ready on port {settings.backend_port}")
    yield
    log.info("GawdBotE shutting down...")


app = FastAPI(
    title="GawdBotE",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{settings.frontend_port}",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# REST ENDPOINTS
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "memory": type(memory).__name__,
        "model": settings.claude_smart_model,
        "version": "0.1.0",
    }


class ChatRequest(BaseModel):
    message: str
    channel: str = "web"
    session_id: str | None = None


@app.post("/chat")
async def chat(req: ChatRequest):
    await memory.save_message("user", req.message, channel=req.channel, session_id=req.session_id)
    response = await orchestrator.process(
        message=req.message,
        channel=req.channel,
        session_id=req.session_id,
    )
    await memory.save_message("assistant", response, channel=req.channel, session_id=req.session_id)
    return {"response": response, "channel": req.channel}


@app.get("/memory/facts")
async def get_facts():
    return {"facts": await memory.get_facts()}


@app.get("/memory/goals")
async def get_goals():
    return {"goals": await memory.get_goals()}


@app.get("/memory/messages")
async def get_messages(limit: int = 50, channel: str | None = None):
    return {"messages": await memory.get_recent_messages(limit=limit, channel=channel)}


@app.delete("/memory/fact/{fact_id}")
async def delete_fact(fact_id: str):
    await memory.delete_memory(fact_id)
    return {"deleted": fact_id}


@app.get("/skills")
async def list_skills():
    from skills.registry import registry
    return {"skills": registry.list_skills()}


@app.post("/skills/{name}/toggle")
async def toggle_skill(name: str, enabled: bool):
    from skills.registry import registry
    registry.set_enabled(name, enabled)
    return {"skill": name, "enabled": enabled}


@app.post("/voice/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe uploaded audio file to text."""
    from voice.stt import transcribe
    audio_bytes = await audio.read()
    text = await transcribe(
        audio_bytes,
        provider=settings.voice_stt_provider,
        groq_api_key=settings.groq_api_key,
        model_size=settings.whisper_model,
    )
    return {"text": text or ""}


@app.post("/vision/screen")
async def analyze_screen_endpoint(question: str = "What is on the screen?"):
    """Capture and analyze the current screen."""
    from vision.screen import analyze_screen
    result = await analyze_screen(
        question=question,
        provider=settings.vision_provider,
        api_key=settings.anthropic_api_key or settings.openai_api_key,
    )
    return {"analysis": result}


# ============================================================
# WEBSOCKET — Real-time chat
# ============================================================

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    log.info("WebSocket client connected")

    try:
        while True:
            data = await ws.receive_json()
            message = data.get("message", "").strip()
            channel = data.get("channel", "web")
            session_id = data.get("session_id")

            if not message:
                continue

            # Typing indicator
            await ws.send_json({"type": "typing", "value": True})

            # Save user message
            await memory.save_message("user", message, channel=channel, session_id=session_id)

            # Process
            response = await orchestrator.process(
                message=message,
                channel=channel,
                session_id=session_id,
            )

            # Save assistant response
            await memory.save_message("assistant", response, channel=channel, session_id=session_id)

            await ws.send_json({
                "type": "message",
                "role": "assistant",
                "content": response,
                "timestamp": datetime.utcnow().isoformat(),
            })

    except WebSocketDisconnect:
        manager.disconnect(ws)
        log.info("WebSocket client disconnected")
    except Exception as e:
        log.error(f"WebSocket error: {e}")
        manager.disconnect(ws)


# ============================================================
# MOBILE — Device registration + Push notifications
# ============================================================

# In-memory device token store (replace with DB for production)
_device_tokens: dict[str, str] = {}  # token -> platform


class DeviceRegisterRequest(BaseModel):
    token: str
    platform: str = "android"


class NotifyRequest(BaseModel):
    token: str
    title: str
    body: str


@app.post("/device/register")
async def register_device(req: DeviceRegisterRequest):
    _device_tokens[req.token] = req.platform
    log.info(f"Device registered: {req.platform} ({req.token[:20]}...)")
    return {"registered": True}


@app.post("/notify")
async def send_notification(req: NotifyRequest):
    """Send a push notification via Expo Push API."""
    import httpx
    payload = {"to": req.token, "title": req.title, "body": req.body, "sound": "default"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://exp.host/--/api/v2/push/send",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
    return resp.json()


@app.get("/device/tokens")
async def get_device_tokens():
    return {"tokens": list(_device_tokens.keys()), "count": len(_device_tokens)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.backend_port,
        reload=False,
        log_level=settings.log_level,
    )
