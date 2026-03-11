"""
GawdBotE — Orchestrator
Routes messages to specialized agent workers based on intent classification.

Intent types:
  research   — web search, summarization, fact-checking
  executor   — code execution, device/file ops
  memory     — explicit store/retrieve memory operations
  creative   — writing, brainstorming, ideas
  critic     — reviewing plans, poking holes
  general    — conversation, questions, everything else
"""

import logging
from datetime import datetime
from pathlib import Path

import anthropic

from config import settings, get_workspace_context, WORKSPACE_DIR

log = logging.getLogger("gawdbote.orchestrator")

INTENT_SYSTEM = """You are an intent classifier for an AI assistant.
Classify the user message into exactly one of these categories:
research, executor, memory, creative, critic, general

Respond with only the category name, nothing else."""

AGENT_NAMES = ["research", "executor", "memory", "creative", "critic", "general"]


class Orchestrator:
    def __init__(self, memory, settings):
        self.memory = memory
        self.settings = settings
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None

    def _build_system_prompt(self, intent: str = "general") -> str:
        workspace = get_workspace_context()
        now = datetime.now().strftime("%A, %B %d %Y %H:%M")

        parts = [
            workspace.get("SOUL", "You are GawdBotE, a super AI partner."),
            f"\nCurrent time: {now}",
        ]

        user_name = self.settings.user_name
        if user_name:
            parts.append(f"You are speaking with {user_name}.")

        # Load user profile if it exists
        profile_path = Path(__file__).parent.parent.parent / "config" / "profile.md"
        if profile_path.exists():
            parts.append(f"\nUser Profile:\n{profile_path.read_text()}")

        if workspace.get("USER"):
            parts.append(f"\nAbout the user:\n{workspace['USER']}")

        # Role-specific instructions
        role_instructions = {
            "research": "\nYou are in RESEARCH mode. Focus on finding accurate information, citing sources, and summarizing findings clearly.",
            "executor": "\nYou are in EXECUTOR mode. Help with code execution, file operations, and device control tasks. Be precise and safe.",
            "memory": "\nYou are in MEMORY mode. Help the user store, organize, and retrieve information from memory.",
            "creative": "\nYou are in CREATIVE mode. Brainstorm freely, explore ideas, and help with writing and creative projects.",
            "critic": "\nYou are in CRITIC mode. Review plans critically, identify weaknesses, and suggest improvements.",
            "general": "",
        }
        parts.append(role_instructions.get(intent, ""))

        parts.append(
            "\n\nMEMORY MANAGEMENT: When the user shares something worth remembering, sets goals, "
            "or completes goals, include these tags in your response (processed automatically):\n"
            "[REMEMBER: fact to store]\n"
            "[GOAL: goal text | DEADLINE: optional date]\n"
            "[DONE: search text for completed goal]"
        )

        return "\n".join(parts)

    async def classify_intent(self, message: str) -> str:
        """Use fast model to classify message intent."""
        if not self._client:
            return "general"
        try:
            resp = self._client.messages.create(
                model=self.settings.claude_fast_model,
                max_tokens=20,
                system=INTENT_SYSTEM,
                messages=[{"role": "user", "content": message}],
            )
            intent = resp.content[0].text.strip().lower()
            return intent if intent in AGENT_NAMES else "general"
        except Exception as e:
            log.error(f"Intent classification error: {e}")
            return "general"

    async def process(
        self,
        message: str,
        channel: str = "web",
        session_id: str | None = None,
    ) -> str:
        """Route message through intent classification → specialized agent → response."""
        if not self._client:
            return "Error: ANTHROPIC_API_KEY not configured. Check your .env file."

        # Classify intent
        intent = await self.classify_intent(message)
        log.info(f"Intent: {intent} | Message: {message[:60]}...")

        # Gather context
        memory_context = await self.memory.get_memory_context()
        semantic_context = await self.memory.semantic_search(message)

        # Build conversation context from recent messages
        recent = await self.memory.get_recent_messages(limit=10, channel=channel)
        # reverse to chronological order
        recent = list(reversed(recent))

        # Build messages list
        messages = []
        for msg in recent:
            if msg["role"] in ("user", "assistant"):
                messages.append({"role": msg["role"], "content": msg["content"]})

        # Append current user message
        prompt_parts = []
        if memory_context:
            prompt_parts.append(memory_context)
        if semantic_context:
            prompt_parts.append(semantic_context)
        prompt_parts.append(message)

        messages.append({"role": "user", "content": "\n\n".join(prompt_parts)})

        system = self._build_system_prompt(intent)

        try:
            resp = self._client.messages.create(
                model=self.settings.claude_smart_model,
                max_tokens=4096,
                system=system,
                messages=messages,
            )
            raw_response = resp.content[0].text
        except Exception as e:
            log.error(f"Claude API error: {e}")
            return f"I encountered an error: {e}"

        # Process memory intent tags
        clean_response = await self.memory.process_memory_intents(raw_response, source=channel)

        return clean_response
