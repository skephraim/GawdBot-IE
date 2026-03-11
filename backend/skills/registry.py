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

    def discover(self):
        """Scan skills/ directory and load available skills."""
        if not SKILLS_DIR.exists():
            return

        for skill_dir in SKILLS_DIR.iterdir():
            if not skill_dir.is_dir():
                continue
            main_py = skill_dir / "main.py"
            if not main_py.exists():
                continue
            try:
                spec = importlib.util.spec_from_file_location(skill_dir.name, main_py)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self._skills[skill_dir.name] = Skill(skill_dir.name, module)
                log.info(f"Loaded skill: {skill_dir.name}")
            except Exception as e:
                log.error(f"Failed to load skill {skill_dir.name}: {e}")

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
