# Test Server - API Endpoint Testing Scripts

This folder contains testing scripts to validate the **Gemma 3n server API endpoints** for different modalities. These scripts test the deployed server's functionality for text generation, image processing, and audio transcription.

## 🎯 Purpose

The scripts in this folder are designed to:
- Test text generation API endpoints
- Validate multimodal image processing capabilities
- Test audio transcription functionality
- Verify server response formats and error handling
- Benchmark API response times

## 🌐 Server Configuration

All scripts are configured to test against a **RunPod deployed server**:
```
SERVER_URL = "https://oqsfk8xvy9emo6-8000.proxy.runpod.net"
```

**⚠️ Important**: Update the `SERVER_URL` in each script to match your actual deployed server endpoint.

## 📋 Prerequisites

Before running these scripts, ensure:
- Python 3.8+ with `requests` library installed
- Server is deployed and accessible
- Network connectivity to the server
- Server endpoints are properly configured

## 🧪 Testing Scripts

### Text Generation Testing

#### `test_text.py`
**Purpose**: Tests the `/generate` endpoint for text generation
```bash
python test_text.py
```

**Features**:
- Tests basic text generation with custom prompts
- Configurable token limits (default: 250 tokens)
- JSON response validation
- Timeout handling (60 seconds)
- Error response parsing

**API Endpoint**: `POST /generate`

**Request Format**:
```json
{
    "prompt": "What is artificial intelligence in short?",
    "max_tokens": 250
}
```

**Expected Response**:
```json
{
    "text": "Generated response text..."
}
```

### Image Processing Testing

#### `test_image.py`
**Purpose**: Tests the `/ask_image` endpoint for image + text processing
```bash
python test_image.py
```

**Features**:
- Downloads test image from Wikipedia
- Tests multimodal image understanding
- Uses multipart form data upload
- Validates image description generation
- Handles file upload errors

**API Endpoint**: `POST /ask_image`

**Request Format**: Multipart form data
- `image`: Image file (PNG/JPG)
- `prompt`: Text prompt for image analysis

**Test Image**: PNG transparency demonstration from Wikipedia

**Expected Response**:
```json
{
    "text": "Image description based on the prompt..."
}
```

### Audio Processing Testing

#### `test_audio.py`
**Purpose**: Tests the `/ask` endpoint for audio transcription
```bash
python test_audio.py
```

**Features**:
- Uses Google's official example audio file
- Downloads WAV file: "roses-are.wav"
- Converts audio to base64 encoding
- Tests audio transcription capabilities
- Handles download and encoding errors

**API Endpoint**: `POST /ask`

**Request Format**:
```json
{
    "data": "base64_encoded_audio_data..."
}
```

**Test Audio**: Google's official Gemma audio example
- URL: `https://ai.google.dev/gemma/docs/audio/roses-are.wav`
- Format: WAV audio file

**Expected Response**:
```json
{
    "text": "Transcribed audio content..."
}
```

## 📝 Usage Instructions

### 1. Update Server URL
Before running any tests, update the `SERVER_URL` in each script:
```python
SERVER_URL = "https://your-actual-server-url.com"
```

### 2. Install Dependencies
```bash
pip install requests
```

### 3. Run Individual Tests

**Test Text Generation**:
```bash
python test_text.py
```

**Test Image Processing**:
```bash
python test_image.py
```

**Test Audio Transcription**:
```bash
python test_audio.py
```

### 4. Run All Tests
```bash
# Run all tests sequentially
python test_text.py && python test_image.py && python test_audio.py
```

## 🔧 Customization

### Modify Test Prompts
Edit the `data` dictionary in each script:

**Text Generation**:
```python
data = {
    "prompt": "Your custom prompt here",
    "max_tokens": 500  # Adjust token limit
}
```

**Image Processing**:
```python
data = {
    'prompt': 'Your custom image analysis prompt'
}
```

### Change Test Files
**Custom Image**: Replace the `image_url` in `test_image.py`:
```python
image_url = "https://your-custom-image-url.com/image.jpg"
```

**Custom Audio**: Replace the `audio_url` in `test_audio.py`:
```python
audio_url = "https://your-custom-audio-url.com/audio.wav"
```

## 🎯 Expected Outputs

### Successful Responses
- ✅ **Status Code**: 200
- ✅ **Response Format**: Valid JSON
- ✅ **Content**: Relevant generated text/description/transcription

### Error Responses
- ❌ **Status Code**: 4xx/5xx
- ❌ **Response**: Error message details
- ❌ **Network**: Connection timeout or failure

## 🔧 Troubleshooting

### Common Issues

**Connection Errors**:
- Verify server URL is correct and accessible
- Check network connectivity
- Ensure server is running and healthy

**Timeout Errors**:
- Increase timeout values (currently 60 seconds)
- Check server performance and load
- Verify model loading is complete

**Response Format Errors**:
- Check server-side JSON formatting
- Verify endpoint implementations
- Review server logs for errors

**File Upload Issues** (Image/Audio):
- Verify file download success
- Check file format compatibility
- Ensure proper multipart encoding

### Debug Tips

1. **Enable Verbose Output**: Add print statements for debugging
2. **Check Server Logs**: Monitor server-side error messages
3. **Test Endpoints Individually**: Isolate issues by testing one modality at a time
4. **Verify File Integrity**: Ensure downloaded test files are valid

## 📊 Performance Expectations

**Typical Response Times**:
- Text Generation: 2-10 seconds (depending on token count)
- Image Processing: 3-8 seconds (including image analysis)
- Audio Transcription: 5-15 seconds (depending on audio length)

**Factors Affecting Performance**:
- Server hardware specifications
- Model loading state (cold vs warm start)
- Network latency
- Input complexity and length

## 🚀 Advanced Usage

### Batch Testing
Create a script to run multiple tests with different inputs:
```python
test_prompts = [
    "Explain AI briefly",
    "What is machine learning?",
    "Describe deep learning"
]

for prompt in test_prompts:
    # Run test with each prompt
```

### Response Time Monitoring
Add timing measurements to track performance:
```python
import time

start_time = time.time()
response = requests.post(...)
response_time = time.time() - start_time
print(f"Response time: {response_time:.2f}s")
```

These testing scripts ensure your Gemma 3n server deployment is working correctly across all supported modalities!
