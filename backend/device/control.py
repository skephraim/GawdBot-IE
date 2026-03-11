"""
GawdBotE — Device Control
Mouse, keyboard, and screen automation via pyautogui.
"""

import logging

log = logging.getLogger("gawdbote.device.control")


def _get_pyautogui():
    try:
        import pyautogui
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        return pyautogui
    except ImportError:
        log.error("pyautogui not installed: pip install pyautogui")
        return None


async def move_mouse(x: int, y: int) -> str:
    pg = _get_pyautogui()
    if not pg:
        return "pyautogui not available"
    pg.moveTo(x, y, duration=0.3)
    return f"Moved mouse to ({x}, {y})"


async def click(x: int | None = None, y: int | None = None, button: str = "left") -> str:
    pg = _get_pyautogui()
    if not pg:
        return "pyautogui not available"
    if x is not None and y is not None:
        pg.click(x, y, button=button)
        return f"Clicked {button} at ({x}, {y})"
    else:
        pg.click(button=button)
        return f"Clicked {button} at current position"


async def type_text(text: str, interval: float = 0.05) -> str:
    pg = _get_pyautogui()
    if not pg:
        return "pyautogui not available"
    pg.typewrite(text, interval=interval)
    return f"Typed: {text[:50]}"


async def press_key(key: str) -> str:
    pg = _get_pyautogui()
    if not pg:
        return "pyautogui not available"
    pg.press(key)
    return f"Pressed: {key}"


async def hotkey(*keys: str) -> str:
    pg = _get_pyautogui()
    if not pg:
        return "pyautogui not available"
    pg.hotkey(*keys)
    return f"Hotkey: {'+'.join(keys)}"


async def scroll(clicks: int, x: int | None = None, y: int | None = None) -> str:
    pg = _get_pyautogui()
    if not pg:
        return "pyautogui not available"
    if x is not None and y is not None:
        pg.scroll(clicks, x=x, y=y)
    else:
        pg.scroll(clicks)
    return f"Scrolled {clicks} clicks"
