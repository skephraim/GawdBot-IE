"""
GawdBotE — FastAPI Backend
REST + WebSocket API for the web dashboard and all interfaces.
"""

import asyncio
import hmac
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import settings
from agents.orchestrator import Orchestrator
from memory.supabase import SupabaseMemory
from memory.local import LocalMemory

# ---- Logging ----
logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
log = logging.getLogger("gawdbote")

# ---- Rate limiting ----
limiter = Limiter(key_func=get_remote_address)

# ---- Auth dependency ----
def require_api_key(request: Request):
    """Reject requests without a valid X-API-Key header."""
    if not settings.api_key:
        raise HTTPException(status_code=500, detail="API_KEY not configured on server")
    provided = request.headers.get("X-API-Key", "")
    if not hmac.compare_digest(provided, settings.api_key):
        raise HTTPException(status_code=401, detail="Unauthorized")

AUTH = Depends(require_api_key)

# ---- Memory backend ----
memory = (
    SupabaseMemory(
        settings.supabase_url,
        settings.supabase_service_key or settings.supabase_anon_key,  # Prefer service key
    )
    if settings.supabase_url and (settings.supabase_service_key or settings.supabase_anon_key)
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
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    # Minimal public response — no internals exposed
    return {"status": "ok"}


class ChatRequest(BaseModel):
    message: str
    channel: str = "web"
    session_id: str | None = None


@app.post("/chat", dependencies=[AUTH])
@limiter.limit("30/minute")
async def chat(request: Request, req: ChatRequest):
    await memory.save_message("user", req.message, channel=req.channel, session_id=req.session_id)
    response = await orchestrator.process(
        message=req.message,
        channel=req.channel,
        session_id=req.session_id,
    )
    await memory.save_message("assistant", response, channel=req.channel, session_id=req.session_id)
    return {"response": response, "channel": req.channel}


@app.get("/memory/facts", dependencies=[AUTH])
async def get_facts():
    return {"facts": await memory.get_facts()}


@app.get("/memory/goals", dependencies=[AUTH])
async def get_goals():
    return {"goals": await memory.get_goals()}


@app.get("/memory/messages", dependencies=[AUTH])
async def get_messages(limit: int = 50, channel: str | None = None):
    limit = min(limit, 200)  # Cap to prevent unbounded queries
    return {"messages": await memory.get_recent_messages(limit=limit, channel=channel)}


@app.delete("/memory/fact/{fact_id}", dependencies=[AUTH])
async def delete_fact(fact_id: str):
    await memory.delete_memory(fact_id)
    return {"deleted": fact_id}


@app.get("/skills", dependencies=[AUTH])
async def list_skills():
    from skills.registry import registry
    return {"skills": registry.list_skills()}


@app.post("/skills/{name}/toggle", dependencies=[AUTH])
async def toggle_skill(name: str, enabled: bool):
    from skills.registry import registry
    registry.set_enabled(name, enabled)
    return {"skill": name, "enabled": enabled}


@app.post("/voice/transcribe", dependencies=[AUTH])
@limiter.limit("20/minute")
async def transcribe_audio(request: Request, audio: UploadFile = File(...)):
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


@app.post("/vision/screen", dependencies=[AUTH])
@limiter.limit("10/minute")
async def analyze_screen_endpoint(request: Request, question: str = "What is on the screen?"):
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
async def websocket_endpoint(ws: WebSocket, api_key: str = ""):
    # Validate API key passed as query param: ws://host/ws?api_key=...
    if not settings.api_key or not hmac.compare_digest(api_key, settings.api_key):
        await ws.close(code=4401)
        return
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


@app.post("/device/register", dependencies=[AUTH])
async def register_device(req: DeviceRegisterRequest):
    if len(_device_tokens) >= 50:  # Hard cap on token count
        raise HTTPException(status_code=400, detail="Token limit reached")
    _device_tokens[req.token] = req.platform
    log.info(f"Device registered: {req.platform}")
    return {"registered": True}


@app.post("/notify", dependencies=[AUTH])
async def send_notification(req: NotifyRequest):
    """Send a push notification via Expo Push API — only to registered tokens."""
    import httpx
    if req.token not in _device_tokens:
        raise HTTPException(status_code=403, detail="Token not registered")
    payload = {"to": req.token, "title": req.title, "body": req.body, "sound": "default"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://exp.host/--/api/v2/push/send",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
    return resp.json()


@app.get("/device/tokens", dependencies=[AUTH])
async def get_device_tokens():
    # Return count only — never enumerate raw tokens
    return {"count": len(_device_tokens)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.backend_port,
        reload=False,
        log_level=settings.log_level,
    )
