"""
GawdBotE — SQLite Memory (Fallback)
Used when Supabase is not configured.
Same interface as SupabaseMemory.
"""

import re
import json
import logging
import sqlite3
from pathlib import Path
from datetime import datetime

log = logging.getLogger("gawdbote.memory.local")


class LocalMemory:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path).expanduser()
        self._conn: sqlite3.Connection | None = None

    async def initialize(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()
        log.info(f"SQLite memory initialized at {self.db_path}")

    def _create_tables(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                created_at TEXT DEFAULT (datetime('now')),
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                channel TEXT DEFAULT 'web',
                session_id TEXT,
                metadata TEXT DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_messages_channel ON messages(channel);

            CREATE TABLE IF NOT EXISTS memory (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT DEFAULT 'chat',
                deadline TEXT,
                completed_at TEXT,
                priority INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_memory_type ON memory(type);

            CREATE TABLE IF NOT EXISTS logs (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                created_at TEXT DEFAULT (datetime('now')),
                level TEXT DEFAULT 'info',
                event TEXT NOT NULL,
                message TEXT,
                metadata TEXT DEFAULT '{}',
                session_id TEXT,
                duration_ms INTEGER
            );
        """)
        self._conn.commit()

    def _row_to_dict(self, row) -> dict:
        return dict(row) if row else {}

    # ---- Core CRUD ----

    async def save_message(
        self,
        role: str,
        content: str,
        channel: str = "web",
        session_id: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        try:
            self._conn.execute(
                "INSERT INTO messages (role, content, channel, session_id, metadata) VALUES (?,?,?,?,?)",
                (role, content, channel, session_id, json.dumps(metadata or {})),
            )
            self._conn.commit()
        except Exception as e:
            log.error(f"save_message error: {e}")

    async def get_recent_messages(self, limit: int = 20, channel: str | None = None) -> list[dict]:
        try:
            if channel:
                rows = self._conn.execute(
                    "SELECT id,created_at,role,content,channel FROM messages WHERE channel=? ORDER BY created_at DESC LIMIT ?",
                    (channel, limit),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT id,created_at,role,content,channel FROM messages ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [self._row_to_dict(r) for r in rows]
        except Exception as e:
            log.error(f"get_recent_messages error: {e}")
            return []

    async def get_facts(self) -> list[dict]:
        try:
            rows = self._conn.execute(
                "SELECT id, content FROM memory WHERE type='fact' ORDER BY created_at DESC"
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]
        except Exception as e:
            log.error(f"get_facts error: {e}")
            return []

    async def get_goals(self) -> list[dict]:
        try:
            rows = self._conn.execute(
                "SELECT id, content, deadline, priority FROM memory WHERE type='goal' ORDER BY priority DESC, created_at DESC"
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]
        except Exception as e:
            log.error(f"get_goals error: {e}")
            return []

    async def store_fact(self, content: str, source: str = "chat") -> None:
        try:
            self._conn.execute(
                "INSERT INTO memory (type, content, source) VALUES ('fact',?,?)",
                (content, source),
            )
            self._conn.commit()
            log.info(f"Stored fact: {content[:60]}")
        except Exception as e:
            log.error(f"store_fact error: {e}")

    async def store_goal(self, content: str, deadline: str | None = None, source: str = "chat") -> None:
        try:
            self._conn.execute(
                "INSERT INTO memory (type, content, deadline, source) VALUES ('goal',?,?,?)",
                (content, deadline, source),
            )
            self._conn.commit()
            log.info(f"Stored goal: {content[:60]}")
        except Exception as e:
            log.error(f"store_goal error: {e}")

    async def mark_goal_done(self, search_text: str) -> None:
        try:
            row = self._conn.execute(
                "SELECT id FROM memory WHERE type='goal' AND content LIKE ? LIMIT 1",
                (f"%{search_text}%",),
            ).fetchone()
            if row:
                self._conn.execute(
                    "UPDATE memory SET type='completed_goal', completed_at=datetime('now') WHERE id=?",
                    (row["id"],),
                )
                self._conn.commit()
        except Exception as e:
            log.error(f"mark_goal_done error: {e}")

    async def delete_memory(self, memory_id: str) -> None:
        try:
            self._conn.execute("DELETE FROM memory WHERE id=?", (memory_id,))
            self._conn.commit()
        except Exception as e:
            log.error(f"delete_memory error: {e}")

    async def semantic_search(self, query: str, table: str = "messages", match_count: int = 5) -> str:
        # No semantic search in SQLite fallback — return empty string
        return ""

    async def get_memory_context(self) -> str:
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

    async def process_memory_intents(self, response: str, source: str = "chat") -> str:
        clean = response

        for match in re.finditer(r"\[REMEMBER:\s*(.+?)\]", response, re.IGNORECASE):
            await self.store_fact(match.group(1).strip(), source=source)
            clean = clean.replace(match.group(0), "")

        for match in re.finditer(
            r"\[GOAL:\s*(.+?)(?:\s*\|\s*DEADLINE:\s*(.+?))?\]", response, re.IGNORECASE
        ):
            await self.store_goal(
                match.group(1).strip(),
                deadline=match.group(2).strip() if match.group(2) else None,
                source=source,
            )
            clean = clean.replace(match.group(0), "")

        for match in re.finditer(r"\[DONE:\s*(.+?)\]", response, re.IGNORECASE):
            await self.mark_goal_done(match.group(1).strip())
            clean = clean.replace(match.group(0), "")

        return clean.strip()

    async def log_event(self, event: str, message: str = "", level: str = "info",
                        metadata: dict | None = None, session_id: str | None = None,
                        duration_ms: int | None = None) -> None:
        try:
            self._conn.execute(
                "INSERT INTO logs (event, message, level, metadata, session_id, duration_ms) VALUES (?,?,?,?,?,?)",
                (event, message, level, json.dumps(metadata or {}), session_id, duration_ms),
            )
            self._conn.commit()
        except Exception as e:
            log.error(f"log_event error: {e}")
