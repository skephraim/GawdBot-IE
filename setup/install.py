#!/usr/bin/env python3
"""
GawdBotE — Install Script
Installs Python and JS dependencies.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

def run(cmd: list[str], cwd: Path | None = None, check: bool = True):
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd or ROOT, check=check)
    return result.returncode == 0

def main():
    print("\n=== GawdBotE Setup ===\n")

    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")

    # Check Bun
    try:
        result = subprocess.run(["bun", "--version"], capture_output=True)
        print(f"✓ Bun {result.stdout.decode().strip()}")
    except FileNotFoundError:
        print("❌ Bun not found. Install: curl -fsSL https://bun.sh/install | bash")
        sys.exit(1)

    # Install Python deps
    print("\n📦 Installing Python dependencies...")
    run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"])
    print("✓ Python deps installed")

    # Install Playwright browsers
    print("\n🌐 Installing Playwright browsers...")
    run([sys.executable, "-m", "playwright", "install", "chromium"], check=False)

    # Install JS deps
    print("\n📦 Installing JS dependencies...")
    run(["bun", "install"])
    print("✓ JS deps installed")

    # Install frontend deps
    print("\n📦 Installing frontend dependencies...")
    run(["bun", "install"], cwd=ROOT / "frontend")
    print("✓ Frontend deps installed")

    # Create .env if needed
    env_path = ROOT / ".env"
    example_path = ROOT / "config" / ".env.example"
    if not env_path.exists() and example_path.exists():
        import shutil
        shutil.copy(example_path, env_path)
        print(f"\n✓ Created .env from example — edit it with your API keys")
    else:
        print(f"\n✓ .env exists")

    # Create workspace memory dir
    (ROOT / "workspace" / "memory").mkdir(exist_ok=True)
    print("✓ workspace/memory/ ready")

    print("\n✅ Installation complete!")
    print("\nNext steps:")
    print("  1. Edit .env with your API keys")
    print("  2. bun run dev:backend   (start backend on :8000)")
    print("  3. bun run dev:frontend  (start web UI on :3000)")
    print("  4. python3 setup/test-connections.py  (verify everything works)")

if __name__ == "__main__":
    main()
