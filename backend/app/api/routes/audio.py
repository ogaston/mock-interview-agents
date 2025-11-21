"""
Audio API routes for voice interview features.
Handles speech-to-text (transcription) and text-to-speech (synthesis).
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.config import settings
import io

router = APIRouter(prefix="/api/audio", tags=["audio"])


class SynthesizeRequest(BaseModel):
    """Request model for text-to-speech synthesis."""
    text: str
    voice_id: str | None = None  # Optional: override default voice


@router.post("/synthesize")
async def synthesize_speech(request: SynthesizeRequest):
    """
    Convert text to speech using configured TTS provider.
    
    Args:
        request: Text to synthesize and optional voice settings
        
    Returns:
        Audio file as streaming response
    """
    if not settings.enable_voice_features:
        raise HTTPException(status_code=403, detail="Voice features are disabled")
    
    if settings.tts_provider == "elevenlabs":
        return await _synthesize_elevenlabs(request.text, request.voice_id)
    elif settings.tts_provider == "openai":
        return await _synthesize_openai(request.text)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported TTS provider: {settings.tts_provider}")


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe audio to text using configured STT provider.
    
    Args:
        file: Audio file upload (mp3, wav, webm, etc.)
        
    Returns:
        Transcribed text
    """
    if not settings.enable_voice_features:
        raise HTTPException(status_code=403, detail="Voice features are disabled")
    
    # Validate file size (max 25MB for OpenAI Whisper)
    contents = await file.read()
    if len(contents) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Audio file too large (max 25MB)")
    
    if settings.stt_provider == "openai":
        return await _transcribe_openai(contents, file.filename)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported STT provider: {settings.stt_provider}")


async def _synthesize_elevenlabs(text: str, voice_id: str | None = None) -> StreamingResponse:
    """Synthesize speech using ElevenLabs API."""
    try:
        from elevenlabs import VoiceSettings
        from elevenlabs.client import ElevenLabs
        
        client = ElevenLabs(api_key=settings.elevenlabs_api_key)
        
        # Use provided voice_id or default
        voice = voice_id or settings.elevenlabs_voice_id
        
        # Generate audio using text_to_speech.convert
        audio_stream = client.text_to_speech.convert(
            text=text,
            voice_id=voice,
            model_id=settings.elevenlabs_model,
            voice_settings=VoiceSettings(
                stability=settings.elevenlabs_stability,
                similarity_boost=settings.elevenlabs_similarity_boost,
            )
        )
        
        # Convert generator to bytes
        audio_bytes = b"".join(audio_stream)
        
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=speech.mp3"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")


async def _synthesize_openai(text: str) -> StreamingResponse:
    """Synthesize speech using OpenAI TTS API."""
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=settings.openai_api_key)
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        
        return StreamingResponse(
            io.BytesIO(response.content),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=speech.mp3"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")


async def _transcribe_openai(audio_bytes: bytes, filename: str) -> dict:
    """Transcribe audio using OpenAI Whisper API."""
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=settings.openai_api_key)
        
        # Create a file-like object
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename
        
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="es"  # Spanish language support
        )
        
        return {"text": transcript.text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
