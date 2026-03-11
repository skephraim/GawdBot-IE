"""
GawdBotE — Text-to-Speech
Supports: piper (local, offline) | elevenlabs (cloud)
"""

import logging
import subprocess
import tempfile
from pathlib import Path

log = logging.getLogger("gawdbote.voice.tts")


async def speak(text: str, provider: str = "piper", **kwargs) -> bytes | None:
    """Convert text to speech, return audio bytes."""
    if provider == "piper":
        return await _speak_piper(text, **kwargs)
    elif provider == "elevenlabs":
        return await _speak_elevenlabs(text, **kwargs)
    else:
        log.error(f"Unknown TTS provider: {provider}")
        return None


async def _speak_piper(text: str, model: str = "en_US-lessac-medium", **kwargs) -> bytes | None:
    """Synthesize via Piper TTS (local, offline)."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            out_path = f.name

        result = subprocess.run(
            ["piper", "--model", model, "--output_file", out_path],
            input=text.encode(),
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            log.error(f"Piper error: {result.stderr.decode()}")
            return None

        audio = Path(out_path).read_bytes()
        Path(out_path).unlink(missing_ok=True)
        return audio

    except FileNotFoundError:
        log.error("piper not installed. Install: https://github.com/rhasspy/piper")
        return None
    except Exception as e:
        log.error(f"Piper TTS error: {e}")
        return None


async def _speak_elevenlabs(
    text: str,
    api_key: str = "",
    voice_id: str = "21m00Tcm4TlvDq8ikWAM",
    **kwargs,
) -> bytes | None:
    """Synthesize via ElevenLabs cloud API."""
    try:
        from elevenlabs import ElevenLabs
        client = ElevenLabs(api_key=api_key)
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_monolingual_v1",
        )
        return b"".join(audio)
    except ImportError:
        log.error("elevenlabs not installed: pip install elevenlabs")
        return None
    except Exception as e:
        log.error(f"ElevenLabs TTS error: {e}")
        return None
