import io
import base64
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from app.config import settings
from app.mocks.audio import generate_mock_audio_bytes

def synthesize_elevenlabs(text: str, voice_id: str | None = None) -> StreamingResponse:
    """Synthesize speech using ElevenLabs API."""
    # Check for mock mode
    if settings.use_mock_tts or settings.tts_provider == "mock":
        mock_audio = generate_mock_audio_bytes()
        return StreamingResponse(
            io.BytesIO(mock_audio),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=speech.mp3"}
        )
    
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
    # Check for mock mode
    if settings.use_mock_tts or settings.tts_provider == "mock":
        mock_audio = generate_mock_audio_bytes()
        return StreamingResponse(
            io.BytesIO(mock_audio),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=speech.mp3"}
        )
    
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


async def synthesize_audio_base64(text: str, voice_id: str | None = None) -> str | None:
    """
    Synthesize speech and return as base64-encoded string.
    
    Args:
        text: Text to synthesize
        voice_id: Optional voice ID override
        
    Returns:
        Base64-encoded audio data or None if voice features disabled
    """
    if not settings.enable_voice_features:
        return None
    
    # Check for mock mode
    if settings.use_mock_tts or settings.tts_provider == "mock":
        mock_audio = generate_mock_audio_bytes()
        return base64.b64encode(mock_audio).decode('utf-8')
    
    try:
        if settings.tts_provider == "elevenlabs":
            from elevenlabs import VoiceSettings
            from elevenlabs.client import ElevenLabs
            
            client = ElevenLabs(api_key=settings.elevenlabs_api_key)
            voice = voice_id or settings.elevenlabs_voice_id
            
            audio_stream = client.text_to_speech.convert(
                text=text,
                voice_id=voice,
                model_id=settings.elevenlabs_model,
                voice_settings=VoiceSettings(
                    stability=settings.elevenlabs_stability,
                    similarity_boost=settings.elevenlabs_similarity_boost,
                )
            )
            audio_bytes = b"".join(audio_stream)
            
        elif settings.tts_provider == "openai":
            from openai import OpenAI
            
            client = OpenAI(api_key=settings.openai_api_key)
            response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
            audio_bytes = response.content
        else:
            return None
        
        # Encode to base64
        return base64.b64encode(audio_bytes).decode('utf-8')
        
    except Exception as e:
        # Log error but don't fail the request - return None if synthesis fails
        print(f"Audio synthesis failed: {str(e)}")
        return None
