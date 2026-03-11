"""
GawdBotE — Webcam Capture
Capture a frame from the webcam for vision analysis.
"""

import base64
import logging

log = logging.getLogger("gawdbote.vision.camera")


async def capture_frame(camera_index: int = 0) -> bytes:
    """Capture a single frame from the webcam."""
    try:
        import cv2
        cap = cv2.VideoCapture(camera_index)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            log.error("Could not read from camera")
            return b""

        _, buf = cv2.imencode(".jpg", frame)
        return buf.tobytes()

    except ImportError:
        log.error("opencv-python not installed: pip install opencv-python")
        return b""
    except Exception as e:
        log.error(f"Camera capture error: {e}")
        return b""


async def capture_and_analyze(
    question: str = "What do you see?",
    api_key: str = "",
    model: str = "claude-opus-4-6",
) -> str:
    img_bytes = await capture_frame()
    if not img_bytes:
        return "Could not capture from camera."

    img_b64 = base64.standard_b64encode(img_bytes).decode()

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}},
                    {"type": "text", "text": question},
                ],
            }],
        )
        return resp.content[0].text
    except Exception as e:
        return f"Camera analysis error: {e}"
