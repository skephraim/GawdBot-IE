"""
GawdBotE — Speech-to-Text
Supports: groq (cloud, free tier) | local (faster-whisper)
Ported from claude-telegram-relay/src/transcribe.ts
"""

import logging
import tempfile
from pathlib import Path

log = logging.getLogger("gawdbote.voice.stt")


async def transcribe(audio_bytes: bytes, provider: str = "groq", **kwargs) -> str | None:
    """Transcribe audio bytes to text."""
    if provider == "groq":
        return await _transcribe_groq(audio_bytes, **kwargs)
    elif provider == "local":
        return await _transcribe_local(audio_bytes, **kwargs)
    else:
        log.error(f"Unknown STT provider: {provider}")
        return None


async def _transcribe_groq(audio_bytes: bytes, groq_api_key: str = "", **kwargs) -> str | None:
    """Transcribe via Groq cloud API (Whisper large-v3)."""
    try:
        from groq import Groq
        client = Groq(api_key=groq_api_key)

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        try:
            with open(tmp_path, "rb") as audio_file:
                result = client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=audio_file,
                    response_format="text",
                )
            return str(result).strip() or None
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    except ImportError:
        log.error("groq package not installed: pip install groq")
        return None
    except Exception as e:
        log.error(f"Groq STT error: {e}")
        return None


async def _transcribe_local(
    audio_bytes: bytes,
    model_size: str = "base.en",
    **kwargs,
) -> str | None:
    """Transcribe locally via faster-whisper."""
    try:
        from faster_whisper import WhisperModel

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        try:
            model = WhisperModel(model_size, device="auto")
            segments, _ = model.transcribe(tmp_path)
            text = " ".join(seg.text for seg in segments).strip()
            return text or None
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    except ImportError:
        log.error("faster-whisper not installed: pip install faster-whisper")
        return None
    except Exception as e:
        log.error(f"Local STT error: {e}")
        return None
