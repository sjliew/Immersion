from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import openai
from app.config import settings
from app.config.supabase import supabase
from supabase import create_client
from datetime import datetime

router = APIRouter()

# Initialize OpenAI
client = openai.OpenAI(api_key=settings.openai_api_key)

# Initialize Supabase client with service key
supabase_client = create_client(settings.supabase_url, settings.supabase_service_key)

# Voice configuration
VOICES = {
    "alloy": "Alloy voice - neutral and balanced",
    "echo": "Echo voice - male voice", 
    "fable": "Fable voice - British male accent",
    "onyx": "Onyx voice - deep male voice",
    "nova": "Nova voice - female voice",
    "shimmer": "Shimmer voice - female voice"
}

@router.post("/generate-samples")
async def generate_voice_samples():
    """Generate sample audio files for all voices (run once for setup)"""
    try:
        sample_urls = {}
        
        for voice_id, description in VOICES.items():
            # Generate sample audio
            sample_text = f"Hello, this is a preview of the {voice_id} voice. {description}"
            
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice_id,
                input=sample_text,
                speed=1.0
            )
            
            # Store in Supabase storage
            file_name = f"voice-samples/{voice_id}_sample.mp3"
            
            try:
                # Upload to Supabase storage
                result = supabase_client.storage.from_('audio-library').upload(
                    file_name,
                    response.content,
                    file_options={"content-type": "audio/mpeg", "upsert": "true"}
                )
            except Exception as e:
                # If bucket doesn't exist, create it
                try:
                    supabase_client.storage.create_bucket('audio-library', public=True)
                    result = supabase_client.storage.from_('audio-library').upload(
                        file_name,
                        response.content,
                        file_options={"content-type": "audio/mpeg", "upsert": "true"}
                    )
                except:
                    pass
            
            # Get public URL
            url = supabase_client.storage.from_('audio-library').get_public_url(file_name)
            sample_urls[voice_id] = url
        
        return JSONResponse({
            "status": "success",
            "message": "Voice samples generated successfully",
            "samples": sample_urls
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/samples")
async def get_voice_samples():
    """Get URLs for pre-generated voice samples"""
    try:
        sample_urls = {}
        
        for voice_id in VOICES.keys():
            file_name = f"voice-samples/{voice_id}_sample.mp3"
            url = supabase_client.storage.from_('audio-library').get_public_url(file_name)
            sample_urls[voice_id] = url
        
        return JSONResponse({
            "status": "success",
            "samples": sample_urls
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))