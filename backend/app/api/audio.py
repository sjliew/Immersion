from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from datetime import datetime
import base64
import openai
from app.models import TranscribeRequest, SynthesizeRequest
from app.config import settings
from app.config.supabase import supabase
from app.middleware.auth import get_current_user, optional_auth

router = APIRouter()

# Initialize OpenAI
openai.api_key = settings.openai_api_key
client = openai.OpenAI(api_key=settings.openai_api_key)


@router.post("/transcribe")
async def transcribe_audio(request: TranscribeRequest):
    """Convert speech to text using OpenAI Whisper"""
    try:
        import io
        import httpx
        
        # Handle both audio URL and base64
        if hasattr(request, 'audio_url') and request.audio_url:
            # Download audio from URL
            async with httpx.AsyncClient() as client_http:
                response = await client_http.get(request.audio_url)
                audio_data = response.content
                audio_file = io.BytesIO(audio_data)
                audio_file.name = "audio.m4a"
        else:
            # Decode base64 audio - handle multiple formats
            audio_base64 = request.audio
            # Remove data URL prefix if present
            if "base64," in audio_base64:
                audio_base64 = audio_base64.split("base64,")[1]
            
            # Ensure proper padding
            missing_padding = len(audio_base64) % 4
            if missing_padding:
                audio_base64 += '=' * (4 - missing_padding)
            
            audio_data = base64.b64decode(audio_base64)
            audio_file = io.BytesIO(audio_data)
            # Detect format from request or default to m4a
            if "webm" in request.audio:
                audio_file.name = "audio.webm"
            else:
                audio_file.name = "audio.m4a"
        
        # Use Whisper API
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=request.language if hasattr(request, 'language') else "en"
        )
        
        return {
            "status": "success",
            "data": {
                "transcription": transcription.text,
                "text": transcription.text,  # Backward compatibility
                "confidence": 0.95  # Whisper doesn't provide confidence
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tts")
async def synthesize_speech(
    request: SynthesizeRequest,
    current_user: dict = Depends(optional_auth)
):
    """Convert text to speech using OpenAI TTS"""
    try:
        # Generate speech
        response = client.audio.speech.create(
            model="tts-1",
            voice=request.voice,
            input=request.text,
            speed=1.0
        )
        
        audio_data = response.content
        
        if request.upload and current_user:
            # Upload to storage and return URL
            file_name = f"audio/{current_user['user_id']}/{datetime.utcnow().timestamp()}.mp3"
            audio_url = await supabase.upload_audio(file_name, audio_data, "audio/mpeg")
            
            return {
                "status": "success",
                "data": {
                    "audio_url": audio_url,
                    "url": audio_url  # Backward compatibility
                }
            }
        else:
            # Upload anyway for consistency
            import uuid
            file_name = f"audio/tts/{uuid.uuid4()}.mp3"
            audio_url = await supabase.upload_audio(file_name, audio_data, "audio/mpeg")
            
            return {
                "status": "success",
                "data": {
                    "audio_url": audio_url,
                    "url": audio_url
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversation-audio")
async def generate_conversation_audio(
    dialogue: list,
    current_user: dict = Depends(get_current_user)
):
    """Generate audio for conversation dialogue"""
    try:
        audio_urls = {}
        voice_map = {
            "neighbor": "echo",
            "colleague": "alloy",
            "friend": "nova",
            "stranger": "fable"
        }
        
        for turn in dialogue:
            if turn.get("text") and turn.get("speaker") != "user":
                voice = voice_map.get(turn["speaker"], "nova")
                
                # Generate speech
                response = client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=turn["text"],
                    speed=1.0
                )
                
                # Upload to storage
                file_name = f"conversations/{turn['id']}_{datetime.utcnow().timestamp()}.mp3"
                audio_url = await supabase.upload_audio(
                    file_name,
                    response.content,
                    "audio/mpeg"
                )
                
                audio_urls[str(turn["id"])] = audio_url
        
        return {
            "status": "success",
            "data": audio_urls
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))