"""
GawdBotE — Screen Capture + Vision Analysis
Screenshot + Claude vision or GPT-4V analysis.
"""

import base64
import logging
from pathlib import Path

log = logging.getLogger("gawdbote.vision.screen")


async def screenshot(save_path: str | None = None) -> bytes:
    """Capture a screenshot and return as PNG bytes."""
    try:
        import mss
        with mss.mss() as sct:
            # Capture primary monitor
            monitor = sct.monitors[1]
            img = sct.grab(monitor)
            # Convert to PNG bytes
            from mss.tools import to_png
            png_bytes = to_png(img.rgb, img.size)

        if save_path:
            Path(save_path).write_bytes(png_bytes)

        return png_bytes
    except ImportError:
        log.error("mss not installed: pip install mss")
        return b""
    except Exception as e:
        log.error(f"Screenshot error: {e}")
        return b""


async def analyze_screen(
    question: str = "What is on the screen?",
    provider: str = "claude",
    api_key: str = "",
    model: str = "claude-opus-4-6",
) -> str:
    """Capture screen and analyze with vision model."""
    img_bytes = await screenshot()
    if not img_bytes:
        return "Could not capture screenshot."

    img_b64 = base64.standard_b64encode(img_bytes).decode()

    if provider == "claude":
        return await _analyze_claude(img_b64, question, api_key, model)
    elif provider == "openai":
        return await _analyze_openai(img_b64, question, api_key)
    else:
        return f"Unknown vision provider: {provider}"


async def _analyze_claude(img_b64: str, question: str, api_key: str, model: str) -> str:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_b64}},
                    {"type": "text", "text": question},
                ],
            }],
        )
        return resp.content[0].text
    except Exception as e:
        return f"Vision analysis error: {e}"


async def _analyze_openai(img_b64: str, question: str, api_key: str) -> str:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                    {"type": "text", "text": question},
                ],
            }],
            max_tokens=1024,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"OpenAI vision error: {e}"
