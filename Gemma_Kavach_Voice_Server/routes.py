# routes.py - Add this to your existing routes.py file

from fastapi import HTTPException, UploadFile, File
from pydantic import BaseModel
import time
from utils import (
    transcribe_audio_from_bytes,
    extract_zone_info, 
    get_zone_update,
    generate_hindi_message
)
from fastapi import APIRouter

router = APIRouter()

# Add this response model to your existing models
class VoiceCommandResponse(BaseModel):
    success: bool
    transcription: str
    zone: str = None
    hindi_message: str = None
    error_message: str = None

# Add monitoring status endpoint that frontend is expecting
@router.get("/monitoring/status")
async def get_monitoring_status():
    """Get monitoring system status"""
    return {
        "status": "active",
        "voice_commands": "enabled",
        "database": "connected",
        "zones_available": ["A", "B", "C", "D"],
        "timestamp": time.time()
    }

# Add this endpoint to your existing router
@router.post("/voice-command", response_model=VoiceCommandResponse)
async def process_voice_command(audio: UploadFile = File(...)):
    """
    Process audio file and return zone security update in Hindi
    
    Steps:
    1. Transcribe audio to text
    2. Extract zone information 
    3. Query database for zone updates
    4. Generate Hindi response message
    """
    
    try:
        # Read audio file
        audio_content = await audio.read()
        
        # Step 1: Transcribe audio
        print("🎤 Transcribing audio...")
        transcription = transcribe_audio_from_bytes(audio_content)
        print(f"Transcription: {transcription}")
        
        # Check if transcription failed
        if not transcription or transcription in ["No speech detected", "TRANSCRIPTION_FAILED", "Audio processing failed. Please try recording again."]:
            error_msg = "तकनीकी समस्या के कारण आवाज़ नहीं समझ पाए। कृपया दोबारा कोशिश करें।"
            if transcription == "TRANSCRIPTION_FAILED":
                error_msg = "सर्वर में समस्या है। बाद में कोशिश करें।"
            
            return VoiceCommandResponse(
                success=False,
                transcription=transcription or "No audio detected",
                error_message=error_msg
            )
        
        # Step 2: Extract zone with retries
        for attempt in range(3):
            try:
                zone_info = extract_zone_info(transcription)
                print(f"Zone info: {zone_info}")
                
                # Check if zone extraction was successful AND valid
                if zone_info and zone_info.get("zone") and zone_info["zone"].lower() not in ["none", "unknown", "न/ए"]:
                    final_zone_info = "Mela Zone " + zone_info["zone"]
                    
                    # Step 3: Get zone update from database
                    print(f"🔍 Querying database for {final_zone_info}...")
                    zone_update = get_zone_update(final_zone_info)
                    
                    # Step 4: Generate Hindi message using LLM
                    print(f"🗣️ Generating Hindi message...")
                    hindi_message = generate_hindi_message(zone_update)
                    
                    return VoiceCommandResponse(
                        success=True,
                        transcription=transcription,
                        zone=final_zone_info,
                        hindi_message=hindi_message
                    )
                    
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                continue
            
            if attempt < 2:  # Don't sleep on last attempt
                time.sleep(1)
        
        # All retries failed
        return VoiceCommandResponse(
            success=False,
            transcription=transcription,
            error_message="कृपया दोबारा रिकॉर्ड करें। ज़ोन की जानकारी स्पष्ट नहीं है।"
        )
        
    except Exception as e:
        print(f"❌ Error processing voice command: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process voice command: {str(e)}"
        )