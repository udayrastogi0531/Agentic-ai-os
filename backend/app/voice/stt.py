"""
Uday AI — Speech-to-Text (Whisper)

Uses faster-whisper for efficient speech recognition.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_whisper_model = None


def _get_whisper_model():
    """Lazy-load the Whisper model."""
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            _whisper_model = WhisperModel(
                settings.whisper_model,
                device="auto",
                compute_type="auto",
            )
            logger.info(f"✅ Whisper model loaded: {settings.whisper_model}")
        except ImportError:
            logger.warning("faster-whisper not installed — STT unavailable")
            return None
    return _whisper_model


async def transcribe_audio(audio_bytes: bytes, language: str = "en") -> str:
    """
    Transcribe audio bytes to text.

    Args:
        audio_bytes: Raw audio data (WAV/MP3).
        language: Language code.

    Returns:
        Transcribed text.
    """
    model = _get_whisper_model()
    if model is None:
        return "[STT unavailable — install faster-whisper]"

    # Write to temp file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name

    try:
        segments, info = model.transcribe(
            temp_path,
            language=language,
            beam_size=5,
            vad_filter=True,
        )

        text = " ".join(segment.text for segment in segments)
        logger.info(f"STT transcription ({info.language}): {text[:80]}...")
        return text.strip()

    except Exception as e:
        logger.error(f"STT error: {e}")
        return f"[Transcription error: {e}]"
    finally:
        Path(temp_path).unlink(missing_ok=True)
