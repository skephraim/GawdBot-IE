"""
GawdBotE — Browser Automation
Playwright-based browser control for web tasks.
"""

import logging
from typing import Any

log = logging.getLogger("gawdbote.device.browser")

_browser = None
_page = None


async def get_page(headless: bool = True):
    """Get or create a browser page."""
    global _browser, _page
    try:
        from playwright.async_api import async_playwright
        if _browser is None:
            pw = await async_playwright().start()
            _browser = await pw.chromium.launch(headless=headless)
            _page = await _browser.new_page()
        return _page
    except ImportError:
        log.error("playwright not installed: pip install playwright && playwright install chromium")
        return None


async def navigate(url: str, headless: bool = True) -> str:
    page = await get_page(headless=headless)
    if not page:
        return "Browser not available"
    await page.goto(url)
    return f"Navigated to {url}"


async def get_page_text(url: str | None = None, headless: bool = True) -> str:
    page = await get_page(headless=headless)
    if not page:
        return "Browser not available"
    if url:
        await page.goto(url)
    return await page.inner_text("body")


async def click_element(selector: str, headless: bool = True) -> str:
    page = await get_page(headless=headless)
    if not page:
        return "Browser not available"
    await page.click(selector)
    return f"Clicked: {selector}"


async def fill_input(selector: str, value: str, headless: bool = True) -> str:
    page = await get_page(headless=headless)
    if not page:
        return "Browser not available"
    await page.fill(selector, value)
    return f"Filled {selector} with: {value[:50]}"


async def screenshot_browser(headless: bool = True) -> bytes:
    page = await get_page(headless=headless)
    if not page:
        return b""
    return await page.screenshot()


async def close():
    global _browser, _page
    if _browser:
        await _browser.close()
        _browser = None
        _page = None
