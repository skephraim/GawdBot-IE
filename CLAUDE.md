# GawdBotE — Guided Setup

> Claude Code reads this file automatically.
> Walk the user through setup one phase at a time.
> Ask for what you need, configure everything yourself, confirm each step works before moving on.
> Do NOT dump all phases at once. Let the user control the pace.

---

## What GawdBotE Is

A self-improving, proactive AI partner with:
- **Web dashboard** (Next.js chat UI, memory viewer, skill manager)
- **Telegram bot** (text, voice, images, documents)
- **CLI interface** (terminal chat)
- **Multi-agent orchestration** (research, executor, creative, critic agents)
- **Persistent memory** (Supabase with semantic search, or SQLite fallback)
- **Voice pipeline** (wake word → STT → response → TTS)
- **Device control** (screen, mouse/keyboard, browser automation)
- **Self-improvement** (.learnings/ logs + /evolve command)

---

## Phase 1: Basic Setup (~5 min)

**Goal:** Get the backend running and verify Claude can respond.

**Ask the user:**
1. Do they have an Anthropic API key? (get one at console.anthropic.com)
2. Their first name and timezone

**What you do:**
1. Run `python3 setup/install.py` to install dependencies
2. Open `.env` and set:
   - `ANTHROPIC_API_KEY`
   - `USER_NAME`
   - `USER_TIMEZONE`
3. Start the backend: `cd backend && python3 main.py`
4. Test: `curl http://localhost:8000/health`
5. Test chat: `curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{"message": "Hello!"}'`

**Done when:** `/health` returns `{"status":"ok"}` and chat responds.

---

## Phase 2: Web Dashboard (~3 min)

**Goal:** Get the web UI running at localhost:3000.

**What you do:**
1. `cd frontend && bun install && bun dev`
2. Tell the user to open http://localhost:3000
3. Verify the dashboard shows "Online" status

**Done when:** User can open the dashboard and chat through the web UI.

---

## Phase 3: Memory — Supabase (~12 min, optional)

Without Supabase, GawdBotE uses SQLite (local, no semantic search). With Supabase, you get persistent memory across reinstalls, semantic search, and cloud backup.

**Ask the user:** Do they want to set up Supabase? (Recommended for best experience)

**If yes:**

**Ask for:**
- Supabase Project URL
- Supabase anon public key

**What to tell them:**
1. Go to supabase.com, create a free project
2. Project Settings > API > copy Project URL and anon key

**What you do:**
1. Set `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `.env`
2. Run the schema: tell user to paste `db/schema.sql` in Supabase SQL Editor
   OR use Supabase MCP: `execute_sql` with contents of `db/schema.sql`
3. Restart backend

**Semantic Search (optional, requires OpenAI key):**
- User goes to Supabase dashboard > Settings > Edge Functions > Secrets
- Adds `OPENAI_API_KEY`
- Deploy two Edge Functions for auto-embedding (embed + search)
- Add database webhooks on messages and memory tables

**Done when:** `python3 setup/test-connections.py` shows Supabase ✓

---

## Phase 4: Telegram (~5 min, optional)

**Ask the user:** Do they want the Telegram bot?

**Ask for:**
- Telegram bot token (from @BotFather)
- Their Telegram user ID (from @userinfobot)

**What you do:**
1. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_USER_ID` in `.env`
2. `cd interfaces/telegram && bun install && bun run bot.ts`
3. Tell user to send a message to their bot on Telegram

**Done when:** User gets a response on Telegram.

---

## Phase 5: User Profile (~3 min)

**Ask the user:**
- What they do for work
- How they like to be communicated with (brief/detailed, casual/formal)
- Any time constraints or schedule
- Key projects or goals right now

**What you do:**
1. Copy `config/profile.example.md` to `config/profile.md` (create if it doesn't exist)
2. Fill in `workspace/USER.md` with their answers
3. The backend loads this on every message

**Done when:** `workspace/USER.md` has real context about the user.

---

## Phase 6: Voice (optional, ~10 min)

### STT (Speech-to-Text)

**Option A: Groq (Recommended — free)**
1. User gets API key at console.groq.com
2. Set `VOICE_STT_PROVIDER=groq` and `GROQ_API_KEY` in `.env`

**Option B: Local (offline)**
1. `pip install faster-whisper`
2. Set `VOICE_STT_PROVIDER=local` and `WHISPER_MODEL=base.en`

### TTS (Text-to-Speech)

**Option A: Piper (local, offline)**
1. Install: `brew install piper-tts` or build from source
2. Set `VOICE_TTS_PROVIDER=piper`

**Option B: ElevenLabs (cloud, better quality)**
1. User gets API key at elevenlabs.io
2. Set `VOICE_TTS_PROVIDER=elevenlabs` and `ELEVENLABS_API_KEY`

**Done when:** STT and TTS providers are configured.

---

## Phase 7: Device Control (optional, macOS)

**⚠️ Ask the user before enabling.** Device control lets GawdBotE move your mouse, type, and control apps.

**What you do:**
1. Set `DEVICE_CONTROL_ENABLED=true` in `.env`
2. Grant Accessibility permissions to Terminal/Python in System Preferences > Privacy > Accessibility
3. Playwright: `python3 -m playwright install chromium`

**Done when:** User understands and confirms they want device control enabled.

---

## Phase 8: Always-On Services (~5 min)

**macOS (launchd):**
```bash
# Customize plist with your actual path
sed -i '' "s|REPLACE_WITH_FULL_PATH|$HOME|g" daemon/com.gawdbote.backend.plist
cp daemon/com.gawdbote.backend.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.gawdbote.backend.plist
```

**PM2 (cross-platform):**
```bash
npm install -g pm2
pm2 start daemon/ecosystem.config.js
pm2 save && pm2 startup
```

**Done when:** Backend survives a terminal close.

---

## After Setup

Run the full health check:
```bash
python3 setup/verify.py
```

Summarize what's running. Remind the user:
- Chat at http://localhost:3000
- Memory viewer at http://localhost:3000/memory
- Skills at http://localhost:3000/skills
- `/evolve` command triggers self-improvement (opens a GitHub PR with suggested code changes)

---

## Self-Improvement

When GawdBotE makes mistakes or the user corrects something:
- Log to `.learnings/LEARNINGS.md` or `ERRORS.md`
- The `/evolve` command: reads CLAUDE.md → analyzes patterns → modifies code → opens GitHub PR

To enable GitHub PR creation, set `GITHUB_TOKEN` and `GITHUB_REPO` in `.env`.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Backend won't start | Check Python 3.11+ and `pip install -r requirements.txt` |
| "ANTHROPIC_API_KEY not set" | Edit `.env`, restart backend |
| Telegram not responding | Check token with @BotFather, user ID with @userinfobot |
| SQLite errors | Check `SQLITE_PATH` is writable |
| Frontend can't connect | Make sure backend is running on port 8000 |
| Supabase errors | Verify URL and anon key, check if schema was applied |
