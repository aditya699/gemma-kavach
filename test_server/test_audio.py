import requests
import base64

SERVER_URL = "https://3gdf7gz3vpdp0z-8000.proxy.runpod.net/"

def test_audio_with_custom_prompt():
    """Test audio processing with custom prompt"""
    print("🎵 Testing audio with custom prompt...")
    
    # Use Google's official example audio file
    audio_url = "https://ai.google.dev/gemma/docs/audio/roses-are.wav"
    
    try:
        # Download the audio file
        response = requests.get(audio_url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Failed to download audio: {response.status_code}")
            return
        
        print("✅ Downloaded audio file")
        
        # Convert to base64
        audio_base64 = base64.b64encode(response.content).decode('utf-8')
        print(f"✅ Converted to base64 ({len(audio_base64)} chars)")
        
        # Send to server with custom prompt
        data = {
            "data": audio_base64,
            "prompt": "Translate the following audio to Hindi"
        }
        
        print("🚀 Sending to server...")
        server_response = requests.post(
            f"{SERVER_URL}/ask",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"Status: {server_response.status_code}")
        
        if server_response.status_code == 200:
            result = server_response.json()
            print(f"✅ Response: {result['text']}")
            print(f"✅ Prompt used: {result['prompt_used']}")
        else:
            print(f"❌ Server error: {server_response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_audio_with_custom_prompt()