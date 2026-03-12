"""
GawdBotE — Browser Automation
Playwright-based browser control for web tasks.
"""

import ipaddress
import logging
import re
from urllib.parse import urlparse

log = logging.getLogger("gawdbote.device.browser")


def _require_verified():
    from agents.executor import _current_verified
    if not _current_verified:
        raise PermissionError("Identity not verified. Say your keyword to unlock browser control.")


def _validate_url(url: str) -> str:
    """Only allow https:// URLs to public hosts."""
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http"):
        raise ValueError(f"Only http/https URLs are allowed, got: {parsed.scheme}")
    hostname = parsed.hostname or ""
    # Block private/loopback ranges
    try:
        addr = ipaddress.ip_address(hostname)
        if addr.is_private or addr.is_loopback or addr.is_reserved:
            raise ValueError(f"Private/loopback addresses are not allowed: {hostname}")
    except ValueError as e:
        if "does not appear to be" not in str(e):
            raise  # Re-raise our own errors
    # Block file:// and other schemes already handled above
    if re.search(r'[<>"\']', url):
        raise ValueError("URL contains invalid characters")
    return url

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
    _require_verified()
    safe_url = _validate_url(url)
    page = await get_page(headless=headless)
    if not page:
        return "Browser not available"
    await page.goto(safe_url)
    return f"Navigated to {safe_url}"


async def get_page_text(url: str | None = None, headless: bool = True) -> str:
    _require_verified()
    page = await get_page(headless=headless)
    if not page:
        return "Browser not available"
    if url:
        safe_url = _validate_url(url)
        await page.goto(safe_url)
    return await page.inner_text("body")


async def click_element(selector: str, headless: bool = True) -> str:
    _require_verified()
    page = await get_page(headless=headless)
    if not page:
        return "Browser not available"
    await page.click(selector)
    return f"Clicked: {selector}"


async def fill_input(selector: str, value: str, headless: bool = True) -> str:
    _require_verified()
    page = await get_page(headless=headless)
    if not page:
        return "Browser not available"
    await page.fill(selector, value)
    return f"Filled {selector} with: {value[:50]}"


async def screenshot_browser(headless: bool = True) -> bytes:
    _require_verified()
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
