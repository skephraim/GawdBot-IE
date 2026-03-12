"""
GawdBotE — Executor Agent
Code execution, file operations, device control.
All dangerous functions require verified identity.
"""

import asyncio
import logging
import tempfile
from pathlib import Path

log = logging.getLogger("gawdbote.agents.executor")

# Sandbox: file operations are restricted to this directory
FILE_SANDBOX = Path.home() / ".gawdbote" / "sandbox"

# Set by orchestrator when identity is verified for the current request
_current_verified: bool = False

def set_verified(verified: bool):
    global _current_verified
    _current_verified = verified

def _require_verified(action: str):
    if not _current_verified:
        raise PermissionError(f"Identity not verified. Say your keyword to unlock {action}.")


async def run_python(code: str, timeout: int = 30) -> str:
    """Execute Python code in a subprocess and return output."""
    _require_verified("code execution")
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
        return output[:2000]
    except asyncio.TimeoutError:
        return f"Error: Code execution timed out after {timeout}s"
    except Exception as e:
        return f"Error: {e}"
    finally:
        Path(path).unlink(missing_ok=True)


async def run_shell(command: str, timeout: int = 30) -> str:
    """Run a shell command and return output."""
    _require_verified("shell execution")
    try:
        result = await asyncio.create_subprocess_exec(
            "/bin/sh", "-c", command,  # exec not shell — still needs -c for complex commands
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=timeout)
        return (stdout.decode() + stderr.decode())[:2000]
    except asyncio.TimeoutError:
        return f"Error: Command timed out after {timeout}s"
    except Exception as e:
        return f"Error: {e}"


def _safe_path(path: str) -> Path:
    """Resolve path and ensure it stays within the sandbox directory."""
    FILE_SANDBOX.mkdir(parents=True, exist_ok=True)
    resolved = (FILE_SANDBOX / path).resolve()
    if not str(resolved).startswith(str(FILE_SANDBOX.resolve())):
        raise PermissionError(f"Path '{path}' is outside the sandbox ({FILE_SANDBOX})")
    return resolved


async def read_file(path: str) -> str:
    """Read a file from the sandbox directory."""
    _require_verified("file access")
    try:
        return _safe_path(path).read_text()[:5000]
    except PermissionError as e:
        return f"Permission denied: {e}"
    except Exception as e:
        return f"Error reading file: {e}"


async def write_file(path: str, content: str) -> str:
    """Write content to a file in the sandbox directory."""
    _require_verified("file write")
    try:
        p = _safe_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"Written to {p}"
    except PermissionError as e:
        return f"Permission denied: {e}"
    except Exception as e:
        return f"Error writing file: {e}"
