"""
GawdBotE — Skill Registry
Discovers and loads pluggable skill modules from skills/ directory.
"""

import importlib
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger("gawdbote.skills")

SKILLS_DIR = Path(__file__).parent.parent.parent / "skills"

# Also scan OpenClaw skills directory if it exists
OPENCLAW_SKILLS_DIRS = [
    Path.home() / "openclaw" / "skills",
    Path.home() / ".openclaw" / "skills",
]


class Skill:
    def __init__(self, name: str, module, enabled: bool = True):
        self.name = name
        self.module = module
        self.enabled = enabled
        self.description = getattr(module, "DESCRIPTION", "")
        self.commands = getattr(module, "COMMANDS", [])

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "commands": self.commands,
            "enabled": self.enabled,
        }


class SkillRegistry:
    def __init__(self):
        self._skills: dict[str, Skill] = {}

    def _load_from_dir(self, skills_dir: Path, prefix: str = ""):
        """Load skills from a directory."""
        if not skills_dir.exists():
            return
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            main_py = skill_dir / "main.py"
            if not main_py.exists():
                continue
            name = f"{prefix}{skill_dir.name}" if prefix else skill_dir.name
            try:
                spec = importlib.util.spec_from_file_location(name, main_py)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self._skills[name] = Skill(name, module)
                log.info(f"Loaded skill: {name}")
            except Exception as e:
                log.error(f"Failed to load skill {name}: {e}")

    def discover(self):
        """Scan skills/ directory and OpenClaw skills directories."""
        self._load_from_dir(SKILLS_DIR)
        for openclaw_dir in OPENCLAW_SKILLS_DIRS:
            self._load_from_dir(openclaw_dir, prefix="openclaw/")

    def list_skills(self) -> list[dict]:
        return [s.to_dict() for s in self._skills.values()]

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def set_enabled(self, name: str, enabled: bool):
        if name in self._skills:
            self._skills[name].enabled = enabled

    async def handle_command(self, command: str, args: str, context: dict) -> str | None:
        """Check if any skill handles this command."""
        for skill in self._skills.values():
            if not skill.enabled:
                continue
            if command in skill.commands:
                try:
                    handler = getattr(skill.module, "handle", None)
                    if handler:
                        return await handler(command, args, context)
                except Exception as e:
                    log.error(f"Skill {skill.name} error: {e}")
        return None


registry = SkillRegistry()
registry.discover()
