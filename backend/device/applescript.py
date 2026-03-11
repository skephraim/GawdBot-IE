"""
GawdBotE — macOS AppleScript Control
Run AppleScript via subprocess for macOS app control.
"""

import asyncio
import logging
import subprocess

log = logging.getLogger("gawdbote.device.applescript")


async def run_applescript(script: str) -> str:
    """Run an AppleScript and return output."""
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
    return await run_applescript(f'tell application "{app_name}" to activate')


async def quit_app(app_name: str) -> str:
    return await run_applescript(f'tell application "{app_name}" to quit')


async def get_frontmost_app() -> str:
    return await run_applescript(
        'tell application "System Events" to get name of first application process whose frontmost is true'
    )


async def send_notification(title: str, message: str, subtitle: str = "") -> str:
    script = f'display notification "{message}" with title "{title}"'
    if subtitle:
        script += f' subtitle "{subtitle}"'
    return await run_applescript(script)


async def set_volume(level: int) -> str:
    """Set system volume (0-100)."""
    return await run_applescript(f"set volume output volume {level}")


async def speak_text(text: str) -> str:
    """Use macOS built-in TTS."""
    return await run_applescript(f'say "{text}"')
