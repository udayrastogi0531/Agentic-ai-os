"""
Nidhi — Voice Routes

Endpoints for:
- Speech-to-Text (Whisper STT)
- Text-to-Speech (Piper TTS)
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, status
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.user import User
from app.voice.stt import transcribe_audio
from app.voice.tts import synthesize_speech

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["Voice"])


class TTSRequest(BaseModel):
    text: str


@router.post(
    "/stt",
    summary="Speech-to-text transcription",
)
async def speech_to_text(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """
    Transcribe uploaded audio file (WAV/MP3/M4A) using Whisper.
    """
    try:
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty audio file provided.",
            )

        text = await transcribe_audio(content)
        return {"text": text}
    except Exception as e:
        logger.error(f"STT route error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech transcription failed: {str(e)}",
        )


@router.post(
    "/tts",
    summary="Text-to-speech synthesis",
)
async def text_to_speech(
    data: TTSRequest,
    user: User = Depends(get_current_user),
):
    """
    Synthesize text to speech (WAV format) using Piper TTS.
    """
    try:
        audio_bytes = await synthesize_speech(data.text)
        if not audio_bytes:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="TTS synthesis is currently unavailable or Piper is not installed.",
            )

        return Response(content=audio_bytes, media_type="audio/wav")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS route error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis failed: {str(e)}",
        )
