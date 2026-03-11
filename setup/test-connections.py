#!/usr/bin/env python3
"""
GawdBotE — Connection Test
Verifies all configured services are reachable.
"""

import asyncio
import os
import sys
from pathlib import Path

# Load .env
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "backend"))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

PASS = "✓"
FAIL = "✗"
SKIP = "○"


async def test_anthropic():
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        print(f"  {SKIP} Anthropic — not configured (ANTHROPIC_API_KEY)")
        return False
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}],
        )
        print(f"  {PASS} Anthropic — {resp.content[0].text.strip()[:20]}")
        return True
    except Exception as e:
        print(f"  {FAIL} Anthropic — {e}")
        return False


async def test_supabase():
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_ANON_KEY", "")
    if not url or not key:
        print(f"  {SKIP} Supabase — not configured (will use SQLite fallback)")
        return None
    try:
        from supabase import create_client
        client = create_client(url, key)
        result = client.table("messages").select("id").limit(1).execute()
        print(f"  {PASS} Supabase — messages table accessible")
        return True
    except Exception as e:
        print(f"  {FAIL} Supabase — {e}")
        return False


async def test_sqlite():
    try:
        import sqlite3
        db_path = Path(os.getenv("SQLITE_PATH", "~/.gawdbote/memory.db")).expanduser()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        conn.execute("SELECT 1")
        conn.close()
        print(f"  {PASS} SQLite — {db_path}")
        return True
    except Exception as e:
        print(f"  {FAIL} SQLite — {e}")
        return False


async def test_backend():
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:8000/health", timeout=5)
            data = resp.json()
            print(f"  {PASS} Backend — {data.get('status')} ({data.get('memory')})")
            return True
    except Exception:
        print(f"  {SKIP} Backend — not running (start with: bun run dev:backend)")
        return None


async def test_telegram():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print(f"  {SKIP} Telegram — not configured")
        return None
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
            data = resp.json()
            if data.get("ok"):
                bot_name = data["result"]["username"]
                print(f"  {PASS} Telegram — @{bot_name}")
                return True
            else:
                print(f"  {FAIL} Telegram — {data.get('description')}")
                return False
    except Exception as e:
        print(f"  {FAIL} Telegram — {e}")
        return False


async def main():
    print("\n=== GawdBotE Connection Test ===\n")

    results = await asyncio.gather(
        test_anthropic(),
        test_supabase(),
        test_sqlite(),
        test_backend(),
        test_telegram(),
        return_exceptions=True,
    )

    passed = sum(1 for r in results if r is True)
    failed = sum(1 for r in results if r is False)
    skipped = sum(1 for r in results if r is None)

    print(f"\n{'='*32}")
    print(f"  {passed} passed  {failed} failed  {skipped} skipped")

    if failed > 0:
        print("\n⚠️  Some checks failed. Review .env and try again.")
        sys.exit(1)
    else:
        print("\n✅ All configured services are working!")

if __name__ == "__main__":
    asyncio.run(main())
