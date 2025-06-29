# routes.py - API endpoints for crowd monitoring
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import aiohttp
from utils import (
    save_session_to_gcs, 
    load_session_from_gcs,
    generate_session_id, 
    get_current_timestamp,
    get_verdict,
    check_gcs_connection,
    BUCKET_NAME,
    SESSIONS_PREFIX
)

# Create router
router = APIRouter()

# Gemma server configuration
GEMMA_API_URL = "https://nsl6up9ztcem6h-8000.proxy.runpod.net/ask_image"
CROWD_ANALYSIS_PROMPT = (
    "Carefully examine the image for any signs of crowd danger or stampede risk. "
    "Look specifically for the following indicators:\n"
    "1) Extremely dense crowds or people tightly packed together\n"
    "2) Individuals falling, being pushed, or trampled\n"
    "3) Panic behaviors such as running, shoving, or erratic movement\n"
    "4) Visible signs of fear, distress, or chaos\n"
    "5) Bottlenecks or unsafe crowd flow patterns\n\n"
    "Respond with only one word: 'Yes' if ANY signs of danger are present, or 'No' if none are detected. "
    "Do not explain your answer."
)


# Request model for creating session
class CreateSessionRequest(BaseModel):
    location: str = "Mela Zone B"  # Default location
    operator_name: Optional[str] = "Security Team"

# Response model for session creation
class SessionResponse(BaseModel):
    session_id: str
    status: str
    location: str
    timestamp: str
    message: str

# Response model for frame analysis
class FrameAnalysisResponse(BaseModel):
    session_id: str
    frame_number: int
    analysis_result: str  # "Yes" or "No"
    risk_detected: bool
    updated_risk_score: float
    frames_analyzed: int
    frames_flagged: int
    timestamp: str

# Response model for session status
class SessionStatusResponse(BaseModel):
    session_id: str
    location: str
    operator_name: str
    status: str
    created_at: str
    last_analysis: Optional[str]
    frames_analyzed: int
    frames_flagged: int
    risk_score: float
    verdict: str  # "SAFE", "WATCH", "ALERT"

@router.post("/session/create", response_model=SessionResponse)
async def create_session(request: CreateSessionRequest):
    """
    Create a new crowd monitoring session
    Frontend calls this first before sending frames
    """
    try:
        # Generate unique session ID and timestamp
        session_id = generate_session_id()
        timestamp = get_current_timestamp()
        
        # Create session data
        session_data = {
            "session_id": session_id,
            "location": request.location,
            "operator_name": request.operator_name,
            "status": "created",
            "created_at": timestamp,
            "frames_analyzed": 0,
            "frames_flagged": 0,
            "risk_score": 0.0,
            "gcs_path": f"gs://{BUCKET_NAME}/{SESSIONS_PREFIX}{session_id}.json"
        }
        
        # Save session to GCS
        success = save_session_to_gcs(session_id, session_data)
        
        if not success:
            raise Exception("Failed to save session to cloud storage")
        
        print(f"✅ Created session: {session_id}")
        print(f"📍 Location: {request.location}")
        print(f"👤 Operator: {request.operator_name}")
        
        return SessionResponse(
            session_id=session_id,
            status="created",
            location=request.location,
            timestamp=timestamp,
            message=f"Session created successfully. Saved to cloud storage."
        )
        
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.post("/session/{session_id}/frame", response_model=FrameAnalysisResponse)
async def analyze_frame(session_id: str, frame: UploadFile = File(...)):
    """
    Analyze a single frame for crowd risk
    Frontend sends one image at a time to this endpoint
    """
    try:
        # Load existing session
        session_data = load_session_from_gcs(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        print(f"🧠 Analyzing frame for session: {session_id}")
        
        # Prepare image for Gemma API
        image_content = await frame.read()
        
        # Call Gemma API
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('image', image_content, filename=frame.filename, content_type=frame.content_type)
            data.add_field('prompt', CROWD_ANALYSIS_PROMPT)
            
            async with session.post(GEMMA_API_URL, data=data) as response:
                if response.status != 200:
                    raise Exception(f"Gemma API error: {response.status}")
                
                result = await response.json()
                gemma_response = result.get("text", "").strip().lower()
        
        # Process analysis result
        risk_detected = gemma_response == "yes"
        frame_number = session_data["frames_analyzed"] + 1
        
        # Update session data
        session_data["frames_analyzed"] = frame_number
        if risk_detected:
            session_data["frames_flagged"] += 1
        
        # Calculate risk score (percentage of flagged frames)
        risk_score = (session_data["frames_flagged"] / frame_number) * 100
        session_data["risk_score"] = round(risk_score, 2)
        session_data["last_analysis"] = get_current_timestamp()
        
        # Save updated session
        save_success = save_session_to_gcs(session_id, session_data)
        if not save_success:
            print("⚠️ Failed to save session update")
        
        print(f"📊 Frame {frame_number}: {'🔴 RISK' if risk_detected else '🟢 SAFE'}")
        print(f"📈 Risk Score: {risk_score}% ({session_data['frames_flagged']}/{frame_number})")
        
        return FrameAnalysisResponse(
            session_id=session_id,
            frame_number=frame_number,
            analysis_result=gemma_response,
            risk_detected=risk_detected,
            updated_risk_score=risk_score,
            frames_analyzed=frame_number,
            frames_flagged=session_data["frames_flagged"],
            timestamp=get_current_timestamp()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error analyzing frame: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze frame: {str(e)}")

@router.get("/session/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """
    Get current status and details of a monitoring session
    Frontend can call this to show real-time updates
    """
    try:
        # Load session data from GCS
        session_data = load_session_from_gcs(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Calculate verdict based on risk score
        risk_score = session_data.get("risk_score", 0.0)
        verdict = get_verdict(risk_score)
        
        print(f"📊 Session {session_id} status: {verdict} ({risk_score}%)")
        
        return SessionStatusResponse(
            session_id=session_id,
            location=session_data["location"],
            operator_name=session_data["operator_name"],
            status=session_data["status"],
            created_at=session_data["created_at"],
            last_analysis=session_data.get("last_analysis"),
            frames_analyzed=session_data["frames_analyzed"],
            frames_flagged=session_data["frames_flagged"],
            risk_score=risk_score,
            verdict=verdict
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting session status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session status: {str(e)}")

# Health check for routes
@router.get("/monitoring/status")
async def monitoring_status():
    """Check if monitoring service is available"""
    gcs_info = check_gcs_connection()
    
    return {
        "service": "monitoring",
        "status": "available",
        "gcs": gcs_info,
        "gemma_api": GEMMA_API_URL,
        "endpoints": ["/session/create", "/session/{id}/frame", "/session/{id}"]
    }