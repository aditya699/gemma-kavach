# utils.py - Enhanced utility functions for dual crowd analysis
import json
import uuid
import time
import smtplib
import os
from email.message import EmailMessage
from google.cloud import storage
from typing import Optional, Dict, Any

from dotenv import load_dotenv
load_dotenv()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcs_key.json"

# GCS Configuration
BUCKET_NAME = os.getenv("BUCKET_NAME")
SESSIONS_PREFIX = "sessions/"
FRAMES_PREFIX = "frames/"
FLAGGED_FRAMES_PREFIX = "flagged_frames/"

# Email Configuration
EMAIL_SENDER = "ab0358031@gmail.com"
EMAIL_PASSWORD = os.getenv("GOOGLE_APP_PASSWORD")
EMAIL_RECEIVER = "ab0358031@gmail.com"

# Enhanced Alert thresholds
MIN_FRAMES_FOR_ALERT = 5
RISK_THRESHOLD_FOR_ALERT = 70.0  # Increased threshold for more sophisticated scoring
CRITICAL_FRAMES_THRESHOLD = 2    # Send alert if 2+ CRITICAL frames detected

# Risk scoring weights
RISK_WEIGHTS = {
    "SAFE": 0,
    "MODERATE": 25,
    "HIGH": 60,
    "CRITICAL": 100
}

# Initialize GCS client (singleton pattern)
_storage_client = None
_bucket = None

def get_gcs_bucket():
    """Get GCS bucket instance (initialize once)"""
    global _storage_client, _bucket
    
    if _bucket is None:
        try:
            _storage_client = storage.Client()
            _bucket = _storage_client.bucket(BUCKET_NAME)
            print(f"✅ Connected to GCS bucket: {BUCKET_NAME}")
        except Exception as e:
            print(f"⚠️ GCS connection error: {e}")
            _bucket = None
    
    return _bucket

def calculate_risk_score(session_data: Dict[str, Any]) -> float:
    """
    Calculate sophisticated risk score based on analysis breakdown
    Considers both frequency of risks and severity levels
    """
    try:
        frames_analyzed = session_data.get("frames_analyzed", 0)
        if frames_analyzed == 0:
            return 0.0
            
        breakdown = session_data.get("analysis_breakdown", {})
        risk_levels = breakdown.get("risk_levels", {})
        
        # Calculate weighted score
        total_weighted_score = 0
        for risk_level, count in risk_levels.items():
            weight = RISK_WEIGHTS.get(risk_level, 0)
            total_weighted_score += (count * weight)
        
        # Average weighted score
        average_score = total_weighted_score / frames_analyzed
        
        # Apply additional penalties for concerning patterns
        density_stats = breakdown.get("density_stats", {})
        motion_stats = breakdown.get("motion_stats", {})
        
        # Penalty for high density frames
        high_density_ratio = density_stats.get("High", 0) / frames_analyzed
        if high_density_ratio > 0.3:  # More than 30% high density
            average_score *= 1.2
            
        # Penalty for chaotic motion
        chaotic_ratio = motion_stats.get("Chaotic", 0) / frames_analyzed
        if chaotic_ratio > 0.2:  # More than 20% chaotic
            average_score *= 1.3
            
        # Cap at 100
        return min(round(average_score, 2), 100.0)
        
    except Exception as e:
        print(f"❌ Error calculating risk score: {e}")
        # Fallback to simple calculation
        frames_flagged = session_data.get("frames_flagged", 0)
        return round((frames_flagged / frames_analyzed) * 100, 2) if frames_analyzed > 0 else 0.0

def get_verdict(risk_score: float) -> str:
    """Convert risk score to verdict with enhanced thresholds"""
    if risk_score <= 15:
        return "SAFE"
    elif risk_score <= 40:
        return "WATCH"
    elif risk_score <= 70:
        return "ALERT"
    else:
        return "CRITICAL"

def should_send_alert(session_data: Dict[str, Any]) -> bool:
    """
    Enhanced alert logic considering multiple factors
    """
    frames_analyzed = session_data.get("frames_analyzed", 0)
    risk_score = session_data.get("risk_score", 0.0)
    email_sent = session_data.get("email_sent", False)
    
    if email_sent or frames_analyzed < MIN_FRAMES_FOR_ALERT:
        return False
    
    # Check for high risk score
    if risk_score >= RISK_THRESHOLD_FOR_ALERT:
        return True
    
    # Check for critical frames
    breakdown = session_data.get("analysis_breakdown", {})
    critical_frames = breakdown.get("risk_levels", {}).get("CRITICAL", 0)
    if critical_frames >= CRITICAL_FRAMES_THRESHOLD:
        print(f"🚨 Alert triggered by {critical_frames} CRITICAL frames")
        return True
    
    # Check for concerning patterns (e.g., rapid increase in risk)
    flagged_frames = session_data.get("flagged_frames", [])
    if len(flagged_frames) >= 3:
        # Check if last 3 frames were all flagged (rapid escalation)
        recent_frames = flagged_frames[-3:]
        frame_numbers = [f["frame_number"] for f in recent_frames]
        if len(frame_numbers) == 3 and max(frame_numbers) - min(frame_numbers) <= 2:
            print(f"🚨 Alert triggered by rapid escalation pattern")
            return True
    
    return False

def send_alert_email(session_id: str, session_data: Dict[str, Any]) -> bool:
    """Enhanced alert email with detailed analysis breakdown"""
    try:
        if not EMAIL_PASSWORD:
            print("⚠️ Email password not set. Skipping email notification.")
            return False
            
        print(f"📧 Sending enhanced alert email for session {session_id}...")
        
        # Create email message
        msg = EmailMessage()
        msg["Subject"] = f"🚨 CROWD SAFETY ALERT - {session_data['location']} (Session {session_id})"
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        
        # Get analysis breakdown
        breakdown = session_data.get("analysis_breakdown", {})
        density_stats = breakdown.get("density_stats", {})
        motion_stats = breakdown.get("motion_stats", {})
        risk_levels = breakdown.get("risk_levels", {})
        
        # Build enhanced email body
        body_lines = [
            f"🚨 CROWD SAFETY ALERT 🚨",
            f"",
            f"📍 Location: {session_data['location']}",
            f"👤 Operator: {session_data['operator_name']}",
            f"🆔 Session ID: {session_id}",
            f"⚠️ Verdict: {get_verdict(session_data['risk_score'])}",
            f"📊 Risk Score: {session_data['risk_score']}%",
            f"🕐 Alert Time: {get_current_timestamp()}",
            f"",
            f"📈 ANALYSIS SUMMARY:",
            f"├── Total Frames Analyzed: {session_data['frames_analyzed']}",
            f"├── Flagged Frames: {session_data['frames_flagged']}",
            f"└── Flagging Rate: {round((session_data['frames_flagged'] / session_data['frames_analyzed']) * 100, 1)}%",
            f"",
            f"👥 CROWD DENSITY BREAKDOWN:",
            f"├── High Density: {density_stats.get('High', 0)} frames",
            f"├── Medium Density: {density_stats.get('Medium', 0)} frames",
            f"└── Low Density: {density_stats.get('Low', 0)} frames",
            f"",
            f"🏃 CROWD MOTION BREAKDOWN:",
            f"├── Chaotic Motion: {motion_stats.get('Chaotic', 0)} frames",
            f"└── Calm Motion: {motion_stats.get('Calm', 0)} frames",
            f"",
            f"🚦 RISK LEVEL BREAKDOWN:",
            f"├── CRITICAL: {risk_levels.get('CRITICAL', 0)} frames",
            f"├── HIGH: {risk_levels.get('HIGH', 0)} frames",
            f"├── MODERATE: {risk_levels.get('MODERATE', 0)} frames",
            f"└── SAFE: {risk_levels.get('SAFE', 0)} frames",
            f"",
        ]
        
        # Add flagged frame details
        flagged_frames = session_data.get("flagged_frames", [])
        if flagged_frames:
            body_lines.append("🔍 FLAGGED FRAME DETAILS:")
            for i, frame_info in enumerate(flagged_frames[-5:], 1):  # Show last 5
                body_lines.append(
                    f"{i}. Frame {frame_info['frame_number']}: "
                    f"{frame_info['risk_level']} "
                    f"(Density: {frame_info.get('crowd_density', 'Unknown')}, "
                    f"Motion: {frame_info.get('crowd_motion', 'Unknown')}) "
                    f"@ {frame_info['timestamp']}"
                )
            body_lines.append("")
        
        body_lines.extend([
            f"⚠️ IMMEDIATE ACTION REQUIRED!",
            f"",
            f"Please investigate the situation immediately and take appropriate crowd control measures.",
            f"",
            f"📂 Session Data: gs://{BUCKET_NAME}/{SESSIONS_PREFIX}{session_id}.json",
            f"",
            f"This alert was generated by Gemma Kavach Vision System"
        ])
        
        msg.set_content("\n".join(body_lines))
        
        # Attach recent flagged images
        attachment_count = 0
        for frame_info in flagged_frames[-3:]:  # Last 3 flagged images
            gcs_path = frame_info.get("gcs_path")
            if gcs_path:
                image_data = download_image_from_gcs(gcs_path)
                if image_data:
                    risk_level = frame_info.get('risk_level', 'FLAGGED')
                    filename = f"{risk_level}_frame_{frame_info['frame_number']:03d}.jpg"
                    msg.add_attachment(
                        image_data,
                        maintype="image",
                        subtype="jpeg", 
                        filename=filename
                    )
                    attachment_count += 1
        
        # Send email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
            
        print(f"✅ Enhanced alert email sent! ({attachment_count} images attached)")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send alert email: {e}")
        return False

def save_session_to_gcs(session_id: str, session_data: Dict[str, Any]) -> bool:
    """Save session data to Google Cloud Storage"""
    try:
        bucket = get_gcs_bucket()
        if not bucket:
            raise Exception("GCS bucket not available")
            
        blob_name = f"{SESSIONS_PREFIX}{session_id}.json"
        blob = bucket.blob(blob_name)
        
        # Upload JSON data
        blob.upload_from_string(
            json.dumps(session_data, indent=2),
            content_type='application/json'
        )
        
        return True
        
    except Exception as e:
        print(f"❌ GCS save error: {e}")
        return False

def load_session_from_gcs(session_id: str) -> Optional[Dict[str, Any]]:
    """Load session data from Google Cloud Storage"""
    try:
        bucket = get_gcs_bucket()
        if not bucket:
            raise Exception("GCS bucket not available")
            
        blob_name = f"{SESSIONS_PREFIX}{session_id}.json"
        blob = bucket.blob(blob_name)
        
        if not blob.exists():
            return None
            
        content = blob.download_as_text()
        return json.loads(content)
        
    except Exception as e:
        print(f"❌ GCS load error: {e}")
        return None

def generate_session_id() -> str:
    """Generate unique session ID"""
    return str(uuid.uuid4())[:8]

def get_current_timestamp() -> str:
    """Get current timestamp in standard format"""
    return time.strftime("%Y-%m-%d %H:%M:%S")

def save_flagged_image_to_gcs(session_id: str, frame_number: int, image_content: bytes) -> Optional[str]:
    """Save flagged image to GCS and return the GCS path"""
    try:
        bucket = get_gcs_bucket()
        if not bucket:
            raise Exception("GCS bucket not available")
            
        blob_name = f"{FLAGGED_FRAMES_PREFIX}{session_id}/frame_{frame_number:03d}.jpg"
        blob = bucket.blob(blob_name)
        
        blob.upload_from_string(
            image_content,
            content_type='image/jpeg'
        )
        
        gcs_path = f"gs://{BUCKET_NAME}/{blob_name}"
        return gcs_path
        
    except Exception as e:
        print(f"❌ Error saving flagged image: {e}")
        return None

def download_image_from_gcs(gcs_path: str) -> Optional[bytes]:
    """Download image content from GCS for email attachment"""
    try:
        bucket = get_gcs_bucket()
        if not bucket:
            return None
            
        blob_name = gcs_path.replace(f"gs://{BUCKET_NAME}/", "")
        blob = bucket.blob(blob_name)
        
        if not blob.exists():
            return None
            
        return blob.download_as_bytes()
        
    except Exception as e:
        print(f"❌ Error downloading image from GCS: {e}")
        return None

def check_gcs_connection() -> Dict[str, str]:
    """Check GCS connection status"""
    bucket = get_gcs_bucket()
    
    return {
        "bucket_name": BUCKET_NAME,
        "status": "connected" if bucket else "disconnected",
        "sessions_path": f"gs://{BUCKET_NAME}/{SESSIONS_PREFIX}",
        "frames_path": f"gs://{BUCKET_NAME}/{FRAMES_PREFIX}",
        "flagged_frames_path": f"gs://{BUCKET_NAME}/{FLAGGED_FRAMES_PREFIX}",
        "analysis_type": "dual_crowd_analysis"
    }