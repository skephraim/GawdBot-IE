"""
GawdBotE — Research Agent
Web search + summarization + fact-checking.
"""

import logging
from duckduckgo_search import DDGS

log = logging.getLogger("gawdbote.agents.research")


async def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Search the web via DuckDuckGo (no API key required)."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return results
    except Exception as e:
        log.error(f"Web search error: {e}")
        return []


async def format_search_results(results: list[dict]) -> str:
    if not results:
        return "No results found."
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. **{r.get('title', 'No title')}**")
        lines.append(f"   {r.get('body', '')[:200]}...")
        lines.append(f"   Source: {r.get('href', '')}")
    return "\n".join(lines)
