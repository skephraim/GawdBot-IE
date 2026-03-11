# TOOLS.md — Local Setup Notes

_Skills define how tools work. This file is for your specifics — things unique to this setup._

## What Goes Here

- Camera names and locations
- SSH hosts and aliases
- Preferred TTS voice/speaker
- Device nicknames
- Environment-specific notes

## Capabilities Available

### Device Control
- Mouse/keyboard: pyautogui (requires DEVICE_CONTROL_ENABLED=true in .env)
- Browser: Playwright (headless or visible)
- macOS: AppleScript via subprocess

### Vision
- Screen capture: mss
- Analysis: Claude vision or GPT-4V (set VISION_PROVIDER in .env)

### Voice
- Wake: openwakeword (optional, configure WAKE_WORD in .env)
- STT: Groq or local faster-whisper (set VOICE_STT_PROVIDER)
- TTS: Piper (local) or ElevenLabs (set VOICE_TTS_PROVIDER)

### Memory
- Supabase (primary, with semantic search via Edge Functions)
- SQLite fallback at ~/.gawdbote/memory.db

---

_Add your own notes below as you configure your setup._

## My Setup

_(Fill this in during setup)_
