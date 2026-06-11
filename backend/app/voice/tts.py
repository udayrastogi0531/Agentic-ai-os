"""
Uday AI — Text-to-Speech (Piper TTS)

Uses Piper TTS for fast, natural-sounding speech synthesis.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def synthesize_speech(text: str) -> bytes | None:
    """
    Convert text to speech audio.

    Args:
        text: Text to synthesize.

    Returns:
        Audio bytes (WAV format) or None if TTS unavailable.
    """
    try:
        import subprocess

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name

        # Use piper CLI
        process = subprocess.run(
            [
                "piper",
                "--model", settings.piper_model_path,
                "--output_file", temp_path,
            ],
            input=text,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if process.returncode != 0:
            logger.error(f"Piper TTS error: {process.stderr}")
            return None

        audio_bytes = Path(temp_path).read_bytes()
        Path(temp_path).unlink(missing_ok=True)

        logger.info(f"TTS synthesis: {len(audio_bytes)} bytes for '{text[:50]}...'")
        return audio_bytes

    except FileNotFoundError:
        logger.warning("Piper TTS not installed — TTS unavailable")
        return None
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return None
