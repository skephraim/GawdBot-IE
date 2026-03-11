"""
GawdBotE — Executor Agent
Code execution, file operations, device control.
"""

import asyncio
import logging
import subprocess
import tempfile
from pathlib import Path

log = logging.getLogger("gawdbote.agents.executor")


async def run_python(code: str, timeout: int = 30) -> str:
    """Execute Python code in a subprocess and return output."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        result = await asyncio.create_subprocess_exec(
            "python3", path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=timeout)
        output = stdout.decode() or stderr.decode()
        return output[:2000]  # Truncate long output
    except asyncio.TimeoutError:
        return f"Error: Code execution timed out after {timeout}s"
    except Exception as e:
        return f"Error: {e}"
    finally:
        Path(path).unlink(missing_ok=True)


async def run_shell(command: str, timeout: int = 30) -> str:
    """Run a shell command and return output. Use with caution."""
    try:
        result = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=timeout)
        return (stdout.decode() + stderr.decode())[:2000]
    except asyncio.TimeoutError:
        return f"Error: Command timed out after {timeout}s"
    except Exception as e:
        return f"Error: {e}"


async def read_file(path: str) -> str:
    """Read a file and return its contents."""
    try:
        return Path(path).expanduser().read_text()[:5000]
    except Exception as e:
        return f"Error reading file: {e}"


async def write_file(path: str, content: str) -> str:
    """Write content to a file."""
    try:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"Written to {path}"
    except Exception as e:
        return f"Error writing file: {e}"
