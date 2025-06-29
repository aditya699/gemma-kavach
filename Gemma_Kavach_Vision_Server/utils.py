# utils.py - Utility functions for Gemma Kavach Vision Server
import json
import uuid
import time
from google.cloud import storage
from typing import Optional, Dict, Any
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcs_key.json"

# GCS Configuration
BUCKET_NAME = "gemma3n-raw"
SESSIONS_PREFIX = "sessions/"
FRAMES_PREFIX = "frames/"

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

def check_gcs_connection() -> Dict[str, str]:
    """Check GCS connection status"""
    bucket = get_gcs_bucket()
    
    return {
        "bucket_name": BUCKET_NAME,
        "status": "connected" if bucket else "disconnected",
        "sessions_path": f"gs://{BUCKET_NAME}/{SESSIONS_PREFIX}",
        "frames_path": f"gs://{BUCKET_NAME}/{FRAMES_PREFIX}"
    }