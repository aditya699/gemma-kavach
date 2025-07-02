import requests
import json

# Your working Runpod server URL
SERVER_URL = "https://3gdf7gz3vpdp0z-8000.proxy.runpod.net/"

def test_text_generation():
    """Test text generation"""
    print("🧪 Testing text generation...")
        
    data = {
        "prompt": "Explain the concept of artificial intelligence in short",  # Very simple
        "max_tokens": 100    # Very short
    }
    
    response = requests.post(
        f"{SERVER_URL}/generate",
        json=data,
        headers={"Content-Type": "application/json"},
        timeout=60  # Give it time to generate
    )
    
    print(f"Status: {response.status_code}")
    print(f"Raw response: {response.text}")
    
    if response.status_code == 200:
        try:
            result = response.json()
            print(f"✅ Generated text: {result['text']}")
        except:
            print("❌ Response is not valid JSON")
    else:
        print(f"❌ Error: {response.text}")

if __name__ == "__main__":
    test_text_generation()