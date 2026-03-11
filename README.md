# GawdBotE

Your super AI partner — self-improving, proactive, multi-interface.

## Quick Start

```bash
# 1. Install dependencies
python3 setup/install.py

# 2. Configure (edit .env with your API keys)
cp config/.env.example .env

# 3. Start backend
bun run dev:backend      # http://localhost:8000

# 4. Start web UI
bun run dev:frontend     # http://localhost:3000

# 5. Verify everything
python3 setup/verify.py
```

## Interfaces

| Interface | Command | Description |
|-----------|---------|-------------|
| Web Dashboard | `bun run dev:frontend` | Chat, memory, skills, settings |
| Telegram | `bun run start:telegram` | Telegram bot |
| CLI | `bun run start:cli` | Terminal chat |

## Architecture

```
[Interfaces]  →  [FastAPI Backend]  →  [Agent Workers]
Web / Telegram    Orchestrator          Research
Discord / CLI     Memory (Supabase)     Executor
Voice             WebSocket             Creative / Critic
```

## Configuration

All settings in `.env`. Key variables:

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Required — get at console.anthropic.com |
| `SUPABASE_URL` | Optional — persistent memory with semantic search |
| `TELEGRAM_BOT_TOKEN` | Optional — Telegram interface |
| `VOICE_STT_PROVIDER` | `groq` or `local` |
| `VOICE_TTS_PROVIDER` | `piper` or `elevenlabs` |

## Guided Setup

Open this folder in Claude Code for interactive setup:
```bash
cd ~/GawdBotE && claude
```

Claude reads `CLAUDE.md` and walks you through setup phase by phase.

## Self-Improvement

When GawdBotE makes mistakes or you correct it, logs go to `.learnings/`.
The `/evolve` command reads patterns, suggests code improvements, and opens a GitHub PR.

## Project Structure

```
GawdBotE/
├── backend/          # FastAPI (Python)
│   ├── agents/       # Orchestrator + specialized agents
│   ├── memory/       # Supabase + SQLite backends
│   ├── voice/        # Wake, STT, TTS
│   ├── vision/       # Screen capture, webcam
│   ├── device/       # Mouse/keyboard, browser, AppleScript
│   └── skills/       # Plugin registry
├── frontend/         # Next.js web dashboard
├── interfaces/       # Telegram, Discord, CLI
├── workspace/        # SOUL, USER, AGENTS, MEMORY files
├── db/               # Supabase schema
├── setup/            # Install and test scripts
└── daemon/           # launchd / PM2 configs
```
