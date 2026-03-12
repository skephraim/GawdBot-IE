"""
GawdBotE — macOS AppleScript Control
Run AppleScript via subprocess for macOS app control.
All functions require verified identity and sanitize inputs.
"""

import asyncio
import logging
import re

log = logging.getLogger("gawdbote.device.applescript")

# Allowlist of app names that can be opened/quit
ALLOWED_APPS = {
    "Safari", "Chrome", "Firefox", "Mail", "Calendar", "Notes", "Terminal",
    "Finder", "Music", "Spotify", "Slack", "Messages", "FaceTime", "Photos",
    "TextEdit", "Preview", "Calculator", "Clock", "Maps", "Reminders",
}


def _require_verified():
    from agents.executor import _current_verified
    if not _current_verified:
        raise PermissionError("Identity not verified. Say your keyword to unlock device control.")


def _sanitize_string(value: str, max_len: int = 200) -> str:
    """Remove characters that could escape AppleScript string context."""
    # Strip quotes, backslashes, and shell-dangerous chars
    sanitized = re.sub(r'["\\\n\r]', '', value)
    return sanitized[:max_len]


def _validate_app(app_name: str) -> str:
    """Check app name is in the allowlist."""
    cleaned = _sanitize_string(app_name, 50)
    if cleaned not in ALLOWED_APPS:
        raise ValueError(f"App '{cleaned}' is not in the allowed list: {sorted(ALLOWED_APPS)}")
    return cleaned


async def run_applescript(script: str) -> str:
    """Run an AppleScript and return output."""
    _require_verified()
    try:
        result = await asyncio.create_subprocess_exec(
            "osascript", "-e", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return f"AppleScript error: {stderr.decode().strip()}"
        return stdout.decode().strip()
    except Exception as e:
        return f"Error: {e}"


async def open_app(app_name: str) -> str:
    validated = _validate_app(app_name)
    return await run_applescript(f'tell application "{validated}" to activate')


async def quit_app(app_name: str) -> str:
    validated = _validate_app(app_name)
    return await run_applescript(f'tell application "{validated}" to quit')


async def get_frontmost_app() -> str:
    _require_verified()
    return await run_applescript(
        'tell application "System Events" to get name of first application process whose frontmost is true'
    )


async def send_notification(title: str, message: str, subtitle: str = "") -> str:
    _require_verified()
    safe_title = _sanitize_string(title, 100)
    safe_message = _sanitize_string(message, 300)
    script = f'display notification "{safe_message}" with title "{safe_title}"'
    if subtitle:
        safe_subtitle = _sanitize_string(subtitle, 100)
        script += f' subtitle "{safe_subtitle}"'
    return await run_applescript(script)


async def set_volume(level: int) -> str:
    _require_verified()
    level = max(0, min(100, int(level)))  # Clamp to 0–100
    return await run_applescript(f"set volume output volume {level}")


async def speak_text(text: str) -> str:
    _require_verified()
    safe_text = _sanitize_string(text, 500)
    return await run_applescript(f'say "{safe_text}"')
