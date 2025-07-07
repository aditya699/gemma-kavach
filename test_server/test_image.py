import requests
import json

# Your working Runpod server URL
SERVER_URL = "https://l63p034w6181jc-8000.proxy.runpod.net/"

def test_image_processing():
    """Test image + text processing"""
    print("🖼️ Testing image processing...")
    
    # Download a test image
    image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png"
    image_response = requests.get(image_url)
    
    if image_response.status_code != 200:
        print("❌ Failed to download test image")
        return
    
    # Prepare the multipart form data
    files = {
        'image': ('test.png', image_response.content, 'image/png')
    }
    data = {
        'prompt': 'What do you see in this image? Describe it briefly.'
    }
    
    response = requests.post(
        f"{SERVER_URL}/ask_image",
        files=files,
        data=data,
        timeout=60
    )
    
    print(f"Status: {response.status_code}")
    print(f"Raw response: {response.text}")
    
    if response.status_code == 200:
        try:
            result = response.json()
            print(f"✅ Image description: {result['text']}")
        except:
            print("❌ Response is not valid JSON")
    else:
        print(f"❌ Error: {response.text}")

if __name__ == "__main__":
    test_image_processing()