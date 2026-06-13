"""
Nidhi — Wake Word Detection

Detects "Hey Uday" wake word using openwakeword.
"""

from __future__ import annotations

import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class WakeWordDetector:
    """
    Detects the "Hey Uday" wake word from audio streams.

    Uses openwakeword library for efficient on-device detection.
    For browser-based detection, this runs on the frontend using
    the Web Audio API with keyword spotting.
    """

    def __init__(self):
        self._model = None
        self._is_available = False

    def initialize(self) -> bool:
        """Initialize the wake word model."""
        try:
            import openwakeword
            from openwakeword.model import Model

            self._model = Model(
                wakeword_models=["hey_jarvis"],  # Closest available model
                inference_framework="onnx",
            )
            self._is_available = True
            logger.info("✅ Wake word detector initialized")
            return True

        except ImportError:
            logger.warning("openwakeword not installed — wake word unavailable")
            return False
        except Exception as e:
            logger.error(f"Wake word init failed: {e}")
            return False

    def detect(self, audio_chunk: bytes) -> bool:
        """
        Check if a wake word is present in an audio chunk.

        Args:
            audio_chunk: Raw audio bytes (16kHz, 16-bit, mono).

        Returns:
            True if wake word detected.
        """
        if not self._is_available or not self._model:
            return False

        try:
            import numpy as np

            audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
            prediction = self._model.predict(audio_array)

            # Check if any wake word score exceeds threshold
            for key, score in prediction.items():
                if score > 0.5:
                    logger.info(f"Wake word detected! ({key}: {score:.3f})")
                    return True

            return False

        except Exception as e:
            logger.error(f"Wake word detection error: {e}")
            return False


# Singleton
wake_word_detector = WakeWordDetector()
