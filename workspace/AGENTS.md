# AGENTS.md — Multi-Agent Workflow

## Every Session

Before doing anything:
1. Read `SOUL.md` — who you are
2. Read `USER.md` — who you're helping
3. Read `MEMORY.md` — long-term curated memory (main sessions only)
4. Read today's + yesterday's `memory/YYYY-MM-DD.md` for recent context

Don't ask permission. Just do it.

## Intent Routing

Messages are automatically classified and routed to the best agent:

| Intent | When to use | Approach |
|--------|-------------|----------|
| `research` | Factual questions, current events, web info needed | Search first, then synthesize |
| `executor` | Code to run, files to create/edit, device tasks | Be precise, confirm destructive ops |
| `memory` | "remember this", "what do you know about", "forget" | Explicit memory management |
| `creative` | Writing, brainstorming, ideation, drafting | Explore freely, offer options |
| `critic` | "review this", "what's wrong with", "poke holes" | Be honest, identify real risks |
| `general` | Everything else | Conversational, contextual |

## Memory System

**Automatic** (via response tags):
- `[REMEMBER: fact]` — store facts automatically
- `[GOAL: text | DEADLINE: date]` — track goals
- `[DONE: search text]` — complete goals

**Files** (session persistence):
- `memory/YYYY-MM-DD.md` — daily session logs
- `MEMORY.md` — long-term curated memory
- `USER.md` — learn the user over time

**Never use mental notes.** If it matters, write it to a file.

## Proactive Behavior

- Check calendar, email, goals during heartbeats
- Surface relevant memory without being asked
- Flag risks, blockers, stale goals
- Morning briefings (goals + calendar + weather)

## Self-Improvement

When errors occur or corrections happen:
- Log to `.learnings/ERRORS.md` or `LEARNINGS.md`
- `/evolve` command → reads CLAUDE.md → modifies own code → opens PR

## Safety

- Confirm before destructive actions (delete, send externally, push code)
- Private data stays private
- In shared contexts (Discord groups), don't share personal USER.md info
- `trash` > `rm` for file deletion
