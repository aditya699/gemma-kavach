# utils.py - Utility functions for Gemma Kavach Vision Server
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
EMAIL_PASSWORD = os.getenv("GOOGLE_APP_PASSWORD")  # Set this in environment
EMAIL_RECEIVER = "ab0358031@gmail.com"

# Alert thresholds
MIN_FRAMES_FOR_ALERT = 5
RISK_THRESHOLD_FOR_ALERT = 60.0

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
        
        print(f"💾 Saved session to GCS: gs://{BUCKET_NAME}/{blob_name}")
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
            print(f"⚠️ Session not found: {session_id}")
            return None
            
        # Download and parse JSON data
        content = blob.download_as_text()
        session_data = json.loads(content)
        
        print(f"📂 Loaded session from GCS: {session_id}")
        return session_data
        
    except Exception as e:
        print(f"❌ GCS load error: {e}")
        return None

def generate_session_id() -> str:
    """Generate unique session ID"""
    return str(uuid.uuid4())[:8]

def get_current_timestamp() -> str:
    """Get current timestamp in standard format"""
    return time.strftime("%Y-%m-%d %H:%M:%S")

def get_verdict(risk_score: float) -> str:
    """Convert risk score to verdict"""
    if risk_score <= 10:
        return "SAFE"
    elif risk_score <= 30:
        return "WATCH"
    else:
        return "ALERT"

def save_flagged_image_to_gcs(session_id: str, frame_number: int, image_content: bytes) -> Optional[str]:
    """Save flagged image to GCS and return the GCS path"""
    try:
        bucket = get_gcs_bucket()
        if not bucket:
            raise Exception("GCS bucket not available")
            
        # Create path: flagged_frames/session_id/frame_001.jpg
        blob_name = f"{FLAGGED_FRAMES_PREFIX}{session_id}/frame_{frame_number:03d}.jpg"
        blob = bucket.blob(blob_name)
        
        # Upload image
        blob.upload_from_string(
            image_content,
            content_type='image/jpeg'
        )
        
        gcs_path = f"gs://{BUCKET_NAME}/{blob_name}"
        print(f"🖼️ Saved flagged image: {gcs_path}")
        return gcs_path
        
    except Exception as e:
        print(f"❌ Error saving flagged image: {e}")
        return None

def get_flagged_images_from_gcs(session_id: str) -> list:
    """Get list of all flagged images for a session"""
    try:
        bucket = get_gcs_bucket()
        if not bucket:
            return []
            
        prefix = f"{FLAGGED_FRAMES_PREFIX}{session_id}/"
        blobs = bucket.list_blobs(prefix=prefix)
        
        images = []
        for blob in blobs:
            if blob.name.endswith('.jpg'):
                images.append({
                    "name": blob.name.split('/')[-1],  # frame_001.jpg
                    "gcs_path": f"gs://{BUCKET_NAME}/{blob.name}",
                    "public_url": f"https://storage.googleapis.com/{BUCKET_NAME}/{blob.name}",
                    "size": blob.size,
                    "created": blob.time_created.strftime("%Y-%m-%d %H:%M:%S") if blob.time_created else None
                })
        
        print(f"📂 Found {len(images)} flagged images for session {session_id}")
        return images
        
    except Exception as e:
        print(f"❌ Error getting flagged images: {e}")
        return []

def download_image_from_gcs(gcs_path: str) -> Optional[bytes]:
    """Download image content from GCS for email attachment"""
    try:
        bucket = get_gcs_bucket()
        if not bucket:
            return None
            
        # Extract blob name from gs://bucket/path
        blob_name = gcs_path.replace(f"gs://{BUCKET_NAME}/", "")
        blob = bucket.blob(blob_name)
        
        if not blob.exists():
            return None
            
        return blob.download_as_bytes()
        
    except Exception as e:
        print(f"❌ Error downloading image from GCS: {e}")
        return None

def should_send_alert(session_data: Dict[str, Any]) -> bool:
    """Check if session meets criteria for sending alert email"""
    frames_analyzed = session_data.get("frames_analyzed", 0)
    risk_score = session_data.get("risk_score", 0.0)
    email_sent = session_data.get("email_sent", False)
    
    return (
        frames_analyzed >= MIN_FRAMES_FOR_ALERT and 
        risk_score >= RISK_THRESHOLD_FOR_ALERT and 
        not email_sent
    )

def send_alert_email(session_id: str, session_data: Dict[str, Any]) -> bool:
    """Send email alert with flagged images attached"""
    try:
        if not EMAIL_PASSWORD:
            print("⚠️ Email password not set. Skipping email notification.")
            return False
            
        print(f"📧 Sending alert email for session {session_id}...")
        
        # Create email message
        msg = EmailMessage()
        msg["Subject"] = f"🚨 CROWD SAFETY ALERT - {session_data['location']} (Session {session_id})"
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        
        # Build email body
        body_lines = [
            f"🚨 CROWD SAFETY ALERT 🚨",
            f"",
            f"Location: {session_data['location']}",
            f"Operator: {session_data['operator_name']}",
            f"Session ID: {session_id}",
            f"Verdict: {get_verdict(session_data['risk_score'])}",
            f"Risk Score: {session_data['risk_score']}%",
            f"Total Frames Analyzed: {session_data['frames_analyzed']}",
            f"Flagged Frames: {session_data['frames_flagged']}",
            f"Alert Time: {get_current_timestamp()}",
            f"",
            f"Flagged Frame Details:",
        ]
        
        # Add flagged frame details
        flagged_frames = session_data.get("flagged_frames", [])
        for frame_info in flagged_frames:
            body_lines.append(f" - Frame {frame_info['frame_number']}: {frame_info['timestamp']}")
            
        body_lines.extend([
            f"",
            f"⚠️ Please investigate immediately!",
            f"",
            f"GCS Session Path: gs://{BUCKET_NAME}/{SESSIONS_PREFIX}{session_id}.json"
        ])
        
        msg.set_content("\n".join(body_lines))
        
        # Attach flagged images
        attachment_count = 0
        for frame_info in flagged_frames[:5]:  # Limit to 5 images to avoid large emails
            gcs_path = frame_info.get("gcs_path")
            if gcs_path:
                image_data = download_image_from_gcs(gcs_path)
                if image_data:
                    filename = f"flagged_frame_{frame_info['frame_number']:03d}.jpg"
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
            
        print(f"✅ Alert email sent successfully! ({attachment_count} images attached)")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send alert email: {e}")
        return False

def check_gcs_connection() -> Dict[str, str]:
    """Check GCS connection status"""
    bucket = get_gcs_bucket()
    
    return {
        "bucket_name": BUCKET_NAME,
        "status": "connected" if bucket else "disconnected",
        "sessions_path": f"gs://{BUCKET_NAME}/{SESSIONS_PREFIX}",
        "frames_path": f"gs://{BUCKET_NAME}/{FRAMES_PREFIX}",
        "flagged_frames_path": f"gs://{BUCKET_NAME}/{FLAGGED_FRAMES_PREFIX}"
    }