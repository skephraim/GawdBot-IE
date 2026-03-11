"""
GawdBotE — Centralized Configuration
Loads from .env at project root or environment variables.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

# Project root: two levels up from backend/
PROJECT_ROOT = Path(__file__).parent.parent
WORKSPACE_DIR = PROJECT_ROOT / "workspace"
LEARNINGS_DIR = PROJECT_ROOT / ".learnings"


class Settings(BaseSettings):
    # ---- LLM ----
    anthropic_api_key: str = ""
    openrouter_api_key: str = ""
    openai_api_key: str = ""

    claude_smart_model: str = "claude-sonnet-4-6"
    claude_fast_model: str = "claude-haiku-4-5-20251001"

    # ---- Memory ----
    supabase_url: str = ""
    supabase_anon_key: str = ""
    sqlite_path: str = str(Path.home() / ".gawdbote" / "memory.db")

    # ---- User ----
    user_name: str = ""
    user_timezone: str = "America/New_York"

    # ---- Interfaces ----
    telegram_bot_token: str = ""
    telegram_user_id: str = ""
    discord_bot_token: str = ""
    discord_guild_id: str = ""
    discord_user_id: str = ""

    # ---- Voice ----
    voice_stt_provider: str = "groq"   # groq | local
    voice_tts_provider: str = "piper"  # piper | elevenlabs
    groq_api_key: str = ""
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""
    whisper_model: str = "base.en"
    piper_model: str = "en_US-lessac-medium"
    wake_word: str = "hey_jarvis"

    # ---- Vision ----
    vision_provider: str = "claude"    # claude | openai

    # ---- Device Control ----
    device_control_enabled: bool = False
    browser_headless: bool = True

    # ---- Services ----
    backend_port: int = 8000
    frontend_port: int = 3000
    log_level: str = "info"

    # ---- Self-Improvement ----
    github_token: str = ""
    github_repo: str = ""

    class Config:
        env_file = str(PROJECT_ROOT / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()


def get_workspace_context() -> dict[str, str]:
    """Load workspace files (SOUL, USER, AGENTS, TOOLS, MEMORY) as system context."""
    files = {
        "SOUL": "SOUL.md",
        "USER": "USER.md",
        "AGENTS": "AGENTS.md",
        "TOOLS": "TOOLS.md",
        "MEMORY": "MEMORY.md",
    }
    context = {}
    for key, filename in files.items():
        path = WORKSPACE_DIR / filename
        if path.exists():
            context[key] = path.read_text()
    return context
