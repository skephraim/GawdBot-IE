"""
GawdBotE — Wake Word Detection
Uses openwakeword for local, always-on detection.
"""

import asyncio
import logging
from typing import Callable

log = logging.getLogger("gawdbote.voice.wake")


class WakeWordDetector:
    def __init__(self, wake_word: str = "hey_jarvis", on_wake: Callable | None = None):
        self.wake_word = wake_word
        self.on_wake = on_wake
        self._running = False

    async def start(self):
        """Start listening for wake word. Calls on_wake() when detected."""
        try:
            import openwakeword
            import pyaudio
            import numpy as np
        except ImportError:
            log.error(
                "Wake word dependencies not installed.\n"
                "Install: pip install openwakeword pyaudio numpy"
            )
            return

        log.info(f"Wake word detector started: '{self.wake_word}'")
        self._running = True

        try:
            from openwakeword.model import Model
            model = Model(wakeword_models=[self.wake_word])

            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1280,
            )

            while self._running:
                raw_audio = stream.read(1280, exception_on_overflow=False)
                audio_chunk = np.frombuffer(raw_audio, dtype=np.int16)
                prediction = model.predict(audio_chunk)

                if prediction.get(self.wake_word, 0) > 0.5:
                    log.info("Wake word detected!")
                    if self.on_wake:
                        await self.on_wake()
                    # Brief pause after detection
                    await asyncio.sleep(1)

                await asyncio.sleep(0)  # yield to event loop

            stream.stop_stream()
            stream.close()
            audio.terminate()

        except Exception as e:
            log.error(f"Wake word detection error: {e}")

    def stop(self):
        self._running = False
