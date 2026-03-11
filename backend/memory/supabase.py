"""
GawdBotE — Supabase Memory
Persistent facts, goals, messages, and semantic search.
Ported from claude-telegram-relay/src/memory.ts

Memory intent tags (Claude includes in responses, automatically processed):
  [REMEMBER: fact to store]
  [GOAL: text | DEADLINE: date]
  [DONE: search text for completed goal]
"""

import re
import logging
from datetime import datetime
from typing import Any

log = logging.getLogger("gawdbote.memory.supabase")


class SupabaseMemory:
    def __init__(self, url: str, anon_key: str):
        self.url = url
        self.anon_key = anon_key
        self._client = None

    async def initialize(self):
        from supabase import create_client
        self._client = create_client(self.url, self.anon_key)
        log.info("Supabase memory initialized")

    # ---- Core CRUD ----

    async def save_message(
        self,
        role: str,
        content: str,
        channel: str = "web",
        session_id: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        if not self._client:
            return
        try:
            self._client.table("messages").insert({
                "role": role,
                "content": content,
                "channel": channel,
                "session_id": session_id,
                "metadata": metadata or {},
            }).execute()
        except Exception as e:
            log.error(f"save_message error: {e}")

    async def get_recent_messages(
        self,
        limit: int = 20,
        channel: str | None = None,
    ) -> list[dict]:
        if not self._client:
            return []
        try:
            q = self._client.table("messages").select("id,created_at,role,content,channel")
            if channel:
                q = q.eq("channel", channel)
            result = q.order("created_at", desc=True).limit(limit).execute()
            return result.data or []
        except Exception as e:
            log.error(f"get_recent_messages error: {e}")
            return []

    async def get_facts(self) -> list[dict]:
        if not self._client:
            return []
        try:
            result = self._client.rpc("get_facts").execute()
            return result.data or []
        except Exception as e:
            log.error(f"get_facts error: {e}")
            return []

    async def get_goals(self) -> list[dict]:
        if not self._client:
            return []
        try:
            result = self._client.rpc("get_active_goals").execute()
            return result.data or []
        except Exception as e:
            log.error(f"get_goals error: {e}")
            return []

    async def store_fact(self, content: str, source: str = "chat") -> None:
        if not self._client:
            return
        try:
            self._client.table("memory").insert({
                "type": "fact",
                "content": content,
                "source": source,
            }).execute()
        except Exception as e:
            log.error(f"store_fact error: {e}")

    async def store_goal(
        self,
        content: str,
        deadline: str | None = None,
        source: str = "chat",
    ) -> None:
        if not self._client:
            return
        try:
            self._client.table("memory").insert({
                "type": "goal",
                "content": content,
                "deadline": deadline,
                "source": source,
            }).execute()
        except Exception as e:
            log.error(f"store_goal error: {e}")

    async def mark_goal_done(self, search_text: str) -> None:
        if not self._client:
            return
        try:
            result = (
                self._client.table("memory")
                .select("id")
                .eq("type", "goal")
                .ilike("content", f"%{search_text}%")
                .limit(1)
                .execute()
            )
            if result.data:
                self._client.table("memory").update({
                    "type": "completed_goal",
                    "completed_at": datetime.utcnow().isoformat(),
                }).eq("id", result.data[0]["id"]).execute()
        except Exception as e:
            log.error(f"mark_goal_done error: {e}")

    async def delete_memory(self, memory_id: str) -> None:
        if not self._client:
            return
        try:
            self._client.table("memory").delete().eq("id", memory_id).execute()
        except Exception as e:
            log.error(f"delete_memory error: {e}")

    # ---- Semantic Search ----

    async def semantic_search(
        self,
        query: str,
        table: str = "messages",
        match_count: int = 5,
    ) -> str:
        """Search via Supabase Edge Function (embedding generated server-side)."""
        if not self._client:
            return ""
        try:
            result = self._client.functions.invoke(
                "search",
                invoke_options={"body": {"query": query, "match_count": match_count, "table": table}},
            )
            if not result.data:
                return ""
            lines = [f"[{m['role']}]: {m['content']}" for m in result.data]
            return "RELEVANT PAST CONTEXT:\n" + "\n".join(lines)
        except Exception:
            return ""

    # ---- Memory Context for Prompts ----

    async def get_memory_context(self) -> str:
        """Return facts + goals formatted for system prompt injection."""
        facts = await self.get_facts()
        goals = await self.get_goals()
        parts = []
        if facts:
            parts.append("FACTS:\n" + "\n".join(f"- {f['content']}" for f in facts))
        if goals:
            goal_lines = []
            for g in goals:
                deadline = f" (by {g['deadline'][:10]})" if g.get("deadline") else ""
                goal_lines.append(f"- {g['content']}{deadline}")
            parts.append("GOALS:\n" + "\n".join(goal_lines))
        return "\n\n".join(parts)

    # ---- Intent Tag Processing ----

    async def process_memory_intents(self, response: str, source: str = "chat") -> str:
        """
        Parse Claude's response for [REMEMBER:], [GOAL:], [DONE:] tags.
        Saves to Supabase, returns cleaned response.
        """
        clean = response

        # [REMEMBER: fact]
        for match in re.finditer(r"\[REMEMBER:\s*(.+?)\]", response, re.IGNORECASE):
            await self.store_fact(match.group(1).strip(), source=source)
            clean = clean.replace(match.group(0), "")

        # [GOAL: text] or [GOAL: text | DEADLINE: date]
        for match in re.finditer(
            r"\[GOAL:\s*(.+?)(?:\s*\|\s*DEADLINE:\s*(.+?))?\]", response, re.IGNORECASE
        ):
            await self.store_goal(
                match.group(1).strip(),
                deadline=match.group(2).strip() if match.group(2) else None,
                source=source,
            )
            clean = clean.replace(match.group(0), "")

        # [DONE: search text]
        for match in re.finditer(r"\[DONE:\s*(.+?)\]", response, re.IGNORECASE):
            await self.mark_goal_done(match.group(1).strip())
            clean = clean.replace(match.group(0), "")

        return clean.strip()

    async def log_event(
        self,
        event: str,
        message: str = "",
        level: str = "info",
        metadata: dict | None = None,
        session_id: str | None = None,
        duration_ms: int | None = None,
    ) -> None:
        if not self._client:
            return
        try:
            self._client.table("logs").insert({
                "event": event,
                "message": message,
                "level": level,
                "metadata": metadata or {},
                "session_id": session_id,
                "duration_ms": duration_ms,
            }).execute()
        except Exception as e:
            log.error(f"log_event error: {e}")
