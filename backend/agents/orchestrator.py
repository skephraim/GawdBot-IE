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

import hmac
import time
import anthropic
from openai import AsyncOpenAI

from config import settings, get_workspace_context, WORKSPACE_DIR

log = logging.getLogger("gawdbote.orchestrator")

# In-memory identity sessions: channel -> verified until timestamp
_verified_sessions: dict[str, float] = {}

INTENT_SYSTEM = """You are an intent classifier for an AI assistant.
Classify the user message into exactly one of these categories:
research, executor, memory, creative, critic, general

Respond with only the category name, nothing else."""

AGENT_NAMES = ["research", "executor", "memory", "creative", "critic", "general"]


class Orchestrator:
    def __init__(self, memory, settings):
        self.memory = memory
        self.settings = settings

        if settings.openrouter_api_key:
            self._provider = "openrouter"
            self._client = AsyncOpenAI(
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
            )
        elif settings.anthropic_api_key:
            self._provider = "anthropic"
            self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        else:
            self._provider = None
            self._client = None

    def _is_verified(self, channel: str) -> bool:
        """Check if this channel has an active verified identity session (24h)."""
        expiry = _verified_sessions.get(channel, 0)
        return time.time() < expiry

    def _verify(self, channel: str):
        """Grant verified access for 24 hours."""
        _verified_sessions[channel] = time.time() + 86400
        log.info(f"Identity verified on channel: {channel}")

    def _check_keyword(self, message: str, channel: str) -> bool:
        """Returns True if the message IS exactly the owner keyword (constant-time compare)."""
        keyword = self.settings.owner_keyword
        if not keyword:
            return False
        # Exact match only — no substring search, constant-time to prevent timing attacks
        if hmac.compare_digest(message.strip(), keyword):
            self._verify(channel)
            return True
        return False

    def _build_system_prompt(self, intent: str = "general", verified: bool = False) -> str:
        workspace = get_workspace_context()
        now = datetime.now().strftime("%A, %B %d %Y %H:%M")

        parts = [
            workspace.get("SOUL", "You are GawdBotE, a super AI partner."),
            f"\nCurrent time: {now}",
        ]

        user_name = self.settings.user_name
        if user_name:
            parts.append(f"You are speaking with {user_name}.")

        if verified and self.settings.device_control_enabled:
            parts.append(
                "\n[IDENTITY VERIFIED] The owner has authenticated with their passphrase. "
                "You have full system access: you can control the Mac (mouse, keyboard, apps, volume, notifications), "
                "read/write files, run AppleScript, and execute system commands. "
                "Assist with any system task the owner requests. Be helpful and direct."
            )
        elif self.settings.device_control_enabled:
            parts.append(
                "\n[SYSTEM NOTE] Device control is enabled but identity is not verified. "
                "If the user provides their keyword, full system access will be unlocked."
            )

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

    async def _call_llm(self, model: str, system: str, messages: list, max_tokens: int = 4096) -> str:
        """Call the configured LLM provider and return the response text."""
        if self._provider == "openrouter":
            try:
                resp = await self._client.chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[{"role": "system", "content": system}] + messages,
                )
            except Exception as e:
                # Some models (e.g. Gemma) don't support system role — merge into first user message
                if "400" in str(e) and messages:
                    merged = list(messages)
                    merged[0] = {
                        "role": "user",
                        "content": f"[System instructions: {system}]\n\n{merged[0]['content']}",
                    }
                    resp = await self._client.chat.completions.create(
                        model=model,
                        max_tokens=max_tokens,
                        messages=merged,
                    )
                else:
                    raise
            return resp.choices[0].message.content
        else:
            # Anthropic
            resp = await self._client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            )
            return resp.content[0].text

    async def classify_intent(self, message: str) -> str:
        """Use fast model to classify message intent."""
        if not self._client:
            return "general"
        try:
            text = await self._call_llm(
                model=self.settings.claude_fast_model,
                system=INTENT_SYSTEM,
                messages=[{"role": "user", "content": message}],
                max_tokens=20,
            )
            intent = text.strip().lower()
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
            return "Error: No LLM API key configured. Set OPENROUTER_API_KEY or ANTHROPIC_API_KEY in .env"

        # Check identity keyword
        self._check_keyword(message, channel)
        verified = self._is_verified(channel)

        # Push verified state into executor so hard gates work
        from agents.executor import set_verified
        set_verified(verified)

        # Classify intent
        intent = await self.classify_intent(message)
        log.info(f"Intent: {intent} | Verified: {verified} | Channel: {channel}")

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

        system = self._build_system_prompt(intent, verified=verified)

        try:
            raw_response = await self._call_llm(
                model=self.settings.claude_smart_model,
                system=system,
                messages=messages,
            )
        except Exception as e:
            log.error(f"LLM API error: {e}")
            return "I ran into a problem on my end. Please try again."

        # Process memory intent tags
        clean_response = await self.memory.process_memory_intents(raw_response, source=channel)

        return clean_response
