import requests
import base64

SERVER_URL = "https://xln0ug8mnka0z8-8000.proxy.runpod.net/"

def test_google_audio():
    """Test with Google's official example audio file"""
    print("🎵 Testing with Google's official audio file...")
    
    # Use Google's official example audio file
    audio_url = "https://ai.google.dev/gemma/docs/audio/roses-are.wav"
    
    try:
        # Download the audio file
        response = requests.get(audio_url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Failed to download Google's audio: {response.status_code}")
            return
        
        print("✅ Downloaded Google's audio file")
        
        # Convert to base64
        audio_base64 = base64.b64encode(response.content).decode('utf-8')
        print(f"✅ Converted to base64 ({len(audio_base64)} chars)")
        
        # Send to your server
        data = {"data": audio_base64}
        
        print("🚀 Sending to Gemma 3n server...")
        server_response = requests.post(
            f"{SERVER_URL}/ask",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"Status: {server_response.status_code}")
        print(f"Response: {server_response.text}")
        
        if server_response.status_code == 200:
            result = server_response.json()
            print(f"✅ Audio transcription: {result['text']}")
        else:
            print(f"❌ Server error: {server_response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_google_audio()