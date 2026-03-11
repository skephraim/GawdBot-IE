#!/usr/bin/env python3
"""
GawdBotE — Full Health Check
Verifies the entire setup is working end-to-end.
"""

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "backend"))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass


def check_file(path: Path, label: str) -> bool:
    if path.exists():
        print(f"  ✓ {label}")
        return True
    else:
        print(f"  ✗ {label} — missing: {path}")
        return False


def check_env(key: str, required: bool = False) -> bool:
    val = os.getenv(key, "")
    if val:
        masked = val[:4] + "..." if len(val) > 4 else "***"
        print(f"  ✓ {key} = {masked}")
        return True
    elif required:
        print(f"  ✗ {key} — REQUIRED, not set!")
        return False
    else:
        print(f"  ○ {key} — not set (optional)")
        return True


async def main():
    print("\n=== GawdBotE Health Check ===\n")

    print("📁 Project Structure:")
    files = [
        (ROOT / ".env", ".env"),
        (ROOT / "backend" / "main.py", "backend/main.py"),
        (ROOT / "backend" / "config.py", "backend/config.py"),
        (ROOT / "frontend" / "package.json", "frontend/package.json"),
        (ROOT / "workspace" / "SOUL.md", "workspace/SOUL.md"),
        (ROOT / "db" / "schema.sql", "db/schema.sql"),
    ]
    for path, label in files:
        check_file(path, label)

    print("\n🔑 Environment Variables:")
    check_env("ANTHROPIC_API_KEY", required=True)
    check_env("SUPABASE_URL")
    check_env("SUPABASE_ANON_KEY")
    check_env("TELEGRAM_BOT_TOKEN")
    check_env("GROQ_API_KEY")
    check_env("USER_NAME")
    check_env("USER_TIMEZONE")

    print("\n🔗 Service Connectivity:")
    # Import and run connection tests
    import subprocess
    subprocess.run([sys.executable, str(ROOT / "setup" / "test-connections.py")])

    print("\n📦 Python Dependencies:")
    required_packages = [
        "fastapi", "uvicorn", "anthropic", "pydantic", "aiofiles",
    ]
    for pkg in required_packages:
        try:
            __import__(pkg.replace("-", "_"))
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  ✗ {pkg} — run: pip install {pkg}")

    print("\n✅ Health check complete!")
    print("\nTo start GawdBotE:")
    print("  Backend:  bun run dev:backend")
    print("  Frontend: bun run dev:frontend")
    print("  Telegram: bun run start:telegram")
    print("  CLI:      bun run start:cli")

if __name__ == "__main__":
    asyncio.run(main())
