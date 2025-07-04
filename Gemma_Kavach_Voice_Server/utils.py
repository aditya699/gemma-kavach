# utils.py - Add these functions to your existing utils.py file

import requests
import base64
import pandas as pd

# Add this configuration
SERVER_URL = "https://3gdf7gz3vpdp0z-8000.proxy.runpod.net/"
TEST_MODE = False  # Set to True for offline testing

def transcribe_audio_from_bytes(audio_bytes: bytes, prompt="Transcribe this audio"):
    """Get transcription from audio bytes with error handling and fallback"""
    try:
        # Convert audio to base64
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        
        # Try the main transcription endpoint first
        data = {"data": audio_base64, "prompt": "Transcribe this Hindi audio speech to text. Only return the transcribed text, nothing else."}
        
        print(f"📤 Sending audio data ({len(audio_bytes)} bytes) to RunPod server...")
        response = requests.post(f"{SERVER_URL}ask", json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if "text" in result and result["text"].strip():
                print(f"✅ Transcription successful: {result['text']}")
                return result["text"]
            else:
                print("⚠️ Empty transcription result")
                return "No speech detected"
        else:
            print(f"❌ Transcription API error: {response.status_code} - {response.text}")
            
            # Try alternative endpoint if available
            try:
                alt_data = {"audio_data": audio_base64, "task": "transcribe"}
                alt_response = requests.post(f"{SERVER_URL}/transcribe", json=alt_data, timeout=60)
                if alt_response.status_code == 200:
                    alt_result = alt_response.json()
                    if "text" in alt_result:
                        print(f"✅ Alternative transcription successful: {alt_result['text']}")
                        return alt_result["text"]
            except Exception as alt_e:
                print(f"⚠️ Alternative endpoint also failed: {alt_e}")
            
            # If all fails, return proper error message
            return "TRANSCRIPTION_FAILED"
            
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return "TRANSCRIPTION_FAILED"

def extract_zone_info(text):
    """Extract zone information from transcribed text"""
    prompt = f"""Extract the zone information from this text. Return ONLY the zone letter/number. No other text.

Example:
Input: "जमा जी ज़ोन सी की सिक्योरिटी अपडेट दीजिए प्लीज।"
Output: C

Input: "ज़ोन बी की अपडेट चाहिए"
Output: B

Input: "{text}"
Output:"""

    data = {"prompt": prompt, "max_tokens": 10, "processing_mode": "force_off"}
    
    response = requests.post(f"{SERVER_URL}/generate", json=data, timeout=30)
    
    if response.status_code == 200:
        zone = response.json()["text"].strip()
        # Only accept single English letters/numbers
        if zone and len(zone) <= 2 and zone.isalnum():
            return {"zone": zone}
    
    return None

def get_zone_update(zone_name):
    """Get latest update for the zone from database"""
    try:
        # Load the processed sessions data from CSV
        df = pd.read_csv("sessions_data.csv")
        
        # Convert timestamp columns to datetime for proper sorting
        df['last_analysis'] = pd.to_datetime(df['last_analysis'], errors='coerce')
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        
        # Filter DataFrame to find sessions for the requested zone
        zone_sessions = df[df['location'] == zone_name]
        
        # Check if zone exists in database
        if zone_sessions.empty:
            return f"❌ No data found for {zone_name}. Available zones: {df['location'].unique().tolist()}"
        
        # Sort by last_analysis timestamp and get the most recent session
        latest_session = zone_sessions.sort_values('last_analysis', ascending=True).iloc[-1]
        
        # Extract all relevant data from the latest session row
        session_id = latest_session['session_id']
        risk_score = latest_session['risk_score']
        frames_analyzed = latest_session['frames_analyzed']
        frames_flagged = latest_session['frames_flagged']
        last_update = latest_session['last_analysis']
        operator_name = latest_session.get('operator_name', 'Security Team')
        
        # Calculate additional metrics from the data
        flagging_rate = (frames_flagged / frames_analyzed * 100) if frames_analyzed > 0 else 0
        
        # Get breakdown stats if available
        density_high = latest_session.get('density_high', 0)
        motion_chaotic = latest_session.get('motion_chaotic', 0)
        risk_critical = latest_session.get('risk_critical', 0)
        
        # Determine risk status based on score
        if risk_score <= 15:
            status = "🟢 SAFE"
            status_msg = "operating normally"
        elif risk_score <= 40:
            status = "🟡 WATCH"
            status_msg = "under routine monitoring"
        elif risk_score <= 70:
            status = "🟠 ALERT"
            status_msg = "requires attention"
        else:
            status = "🔴 CRITICAL"
            status_msg = "IMMEDIATE ACTION REQUIRED"
        
        # Create comprehensive update message
        message = f"""
🛡️ {zone_name} Security Update

📊 Current Status: {status}
📈 Risk Score: {risk_score}%
👥 Frames Analyzed: {frames_analyzed}
⚠️ Frames Flagged: {frames_flagged} ({flagging_rate:.1f}%)
🕒 Last Updated: {last_update.strftime('%Y-%m-%d %H:%M:%S')}
👤 Operator: {operator_name}
🆔 Session: {session_id}

📋 Analysis Details:
• High Density Events: {density_high}
• Chaotic Motion Events: {motion_chaotic}  
• Critical Risk Events: {risk_critical}

Status: Zone is currently {status_msg}.
"""
        
        return message.strip()
        
    except FileNotFoundError:
        return "❌ Database file 'sessions_data.csv' not found. Please run the data processor first."
    except Exception as e:
        return f"❌ Error retrieving update for {zone_name}: {str(e)}"

def generate_hindi_message(zone_update_data):
    """Generate user-friendly Hindi message using LLM"""
    try:
        prompt = f"""Convert this security update data into a natural, user-friendly Hindi message for voice response. Make it conversational and easy to understand.

Data: {zone_update_data}

Instructions:
- Convert to natural Hindi 
- Make it sound like a security officer giving an update
- Keep it concise but informative
- Include key status and numbers
- Sound professional but friendly
- Do NOT say "जी हाँ, ज़ोन बी" - just give the update directly
- Start with the current status

Example style: "स्थिति सामान्य है। रिस्क स्कोर 15% है और कोई खतरा नहीं है।"

Hindi Message:"""

        data = {"prompt": prompt, "max_tokens": 150}
        
        response = requests.post(f"{SERVER_URL}/generate", json=data, timeout=30)
        
        if response.status_code == 200:
            hindi_message = response.json()["text"].strip()
            return hindi_message
        else:
            return "अपडेट प्राप्त करने में कुछ समस्या है। कृपया दोबारा कोशिश करें।"
            
    except Exception as e:
        return "तकनीकी समस्या के कारण अपडेट नहीं मिल सका।"