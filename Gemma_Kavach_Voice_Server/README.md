# Voice Command Server - Gemma Kavach

## Overview

The Voice Command Server is a core component of the Gemma Kavach crowd safety suite that enables hands-free voice interactions for security personnel. The system processes Hindi-English voice commands, queries zone security data, and responds with natural Hindi audio feedback powered by Google Text-to-Speech.

## Features

- **🎤 Voice Transcription**: Real-time audio processing using Gemma 3n multimodal capabilities
- **🗣️ Hindi/English Support**: Natural language processing for Indian security contexts
- **📊 Database Integration**: Real-time zone security data retrieval
- **🔊 Text-to-Speech**: Google TTS with Hindi voice responses
- **📱 Mobile Optimized**: Cross-platform audio support (iOS, Android, Desktop)
- **🌐 REST API**: FastAPI-based endpoints for voice command processing

## System Architecture

```
Voice Command Flow:
Audio Input → Transcription → Zone Extraction → Database Query → Hindi Response → TTS Audio
```

### Core Components

1. **FastAPI Server** (`main.py`) - Web server and routing
2. **Voice Routes** (`routes.py`) - Voice command endpoint and processing
3. **Utils** (`utils.py`) - Transcription, TTS, and database utilities
4. **Frontend** (`index.html` + `app.js` + `style.css`) - Voice interface

## Requirements

### Hardware
- **GPU**: RTX 4090 or equivalent (for Gemma 3n inference)
- **RAM**: 16GB+ recommended
- **Storage**: 10GB for models and data

### Software Dependencies

```bash
# Core server dependencies
pip install fastapi uvicorn python-multipart
pip install pandas requests python-dotenv

# Google Cloud TTS (optional)
pip install google-cloud-texttospeech

# For development
pip install python-jose[cryptography] passlib[bcrypt]
```

### External Services

1. **Gemma 3n Inference Server** - Running on RunPod or local GPU
2. **Google Text-to-Speech API** (optional but recommended)
3. **Session Database** - CSV-based zone monitoring data

## Quick Start

### Step 1: Environment Setup

Create a `.env` file:
```bash
# Gemma 3n Server URL (your inference server)
SERVER_URL=https://your-runpod-server.proxy.runpod.net/

# Google TTS API Key (optional)
GOOGLE_TEXT_TO_SPEECH=your_google_tts_api_key

# Server Configuration
HOST=0.0.0.0
PORT=7860
```

### Step 2: Start the Server

```bash
# Start the voice command server
python main.py
```

Server will be available at:
- **Main Interface**: http://localhost:7860
- **API Documentation**: http://localhost:7860/docs
- **Voice Command Endpoint**: http://localhost:7860/api/voice-command

### Step 3: Prepare Zone Data

Ensure you have `sessions_data.csv` with zone monitoring data:
```csv
session_id,location,risk_score,frames_analyzed,frames_flagged,last_analysis,operator_name
session_001,Mela Zone A,15,150,5,2025-07-09 14:30:00,Security Team Alpha
session_002,Mela Zone B,45,200,25,2025-07-09 14:32:00,Security Team Beta
...
```

## API Endpoints

### Voice Command Processing

**POST** `/api/voice-command`

Processes audio files and returns zone security updates with Hindi audio responses.

**Request:**
```http
POST /api/voice-command
Content-Type: multipart/form-data

audio: [audio file - MP4/WAV/WebM]
```

**Response:**
```json
{
  "success": true,
  "transcription": "ज़ोन बी की सिक्योरिटी अपडेट दीजिए",
  "zone": "Mela Zone B",
  "hindi_message": "स्थिति सामान्य है। रिस्क स्कोर 45% है।",
  "audio_content": "base64_encoded_audio_data",
  "error_message": null
}
```

### System Status

**GET** `/api/monitoring/status`

Returns system health and capabilities.

```json
{
  "status": "active",
  "voice_commands": "enabled",
  "text_to_speech": "enabled",
  "database": "connected",
  "zones_available": ["A", "B", "C", "D"],
  "timestamp": 1641234567.89
}
```

## Voice Command Examples

The system supports natural Hindi-English voice commands:

### Supported Commands
- `"ज़ोन बी की सिक्योरिटी अपडेट दीजिए"`
- `"Zone C ka kya haal hai?"`
- `"मुझे ज़ोन ए की जानकारी चाहिए"`
- `"Security update for Zone D please"`

### Audio Format Support
- **iOS Safari**: MP4 (required)
- **Android Chrome**: WebM/MP4
- **Desktop**: WAV/WebM/MP4

## Configuration

### Server Configuration

Edit `main.py` for server settings:
```python
if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0",    # Bind to all interfaces
        port=7860,          # Server port
        reload=True         # Auto-reload on changes
    )
```

### Audio Processing Settings

In `utils.py`, configure transcription:
```python
SERVER_URL = "https://your-gemma-server.com/"
TEST_MODE = False  # Set to True for debugging

def transcribe_audio_from_bytes(audio_bytes: bytes):
    # Configure retry attempts and timeout
    for attempt in range(3):
        response = requests.post(
            f"{SERVER_URL}ask", 
            json=data, 
            timeout=90  # Adjust timeout as needed
        )
```

### Text-to-Speech Settings

Configure Google TTS in `utils.py`:
```python
def generate_speech_audio(text: str, language_code: str = "hi-IN"):
    payload = {
        "voice": {
            "languageCode": language_code,
            "name": "hi-IN-Wavenet-A",  # Hindi female voice
            "ssmlGender": "FEMALE"
        },
        "audioConfig": {
            "audioEncoding": "MP3",
            "speakingRate": 0.9,  # Adjust speed
            "pitch": 0.0,
            "volumeGainDb": 0.0
        }
    }
```

## Database Integration

### Zone Data Structure

The system expects CSV data with these columns:

```python
# Required columns in sessions_data.csv
required_columns = [
    'session_id',         # Unique session identifier
    'location',           # Zone name (e.g., "Mela Zone A")
    'risk_score',         # Risk percentage (0-100)
    'frames_analyzed',    # Total frames processed
    'frames_flagged',     # Flagged frames count
    'last_analysis',      # Timestamp of last update
    'operator_name'       # Security operator name
]
```

### Database Query Function

```python
def get_zone_update(zone_name):
    """
    Retrieves latest zone security data
    Returns formatted security update message
    """
    # Load CSV data
    df = pd.read_csv("sessions_data.csv")
    
    # Filter by zone and get latest data
    zone_data = df[df['location'] == zone_name]
    latest = zone_data.sort_values('last_analysis').iloc[-1]
    
    # Generate status message
    return formatted_security_update
```

## Frontend Interface

### Voice Interface Features

- **🎤 Voice Recording**: One-click recording with visual feedback
- **📱 Mobile Support**: iOS/Android optimized audio handling
- **🔊 Audio Playback**: Automatic TTS response playback
- **📊 Real-time Status**: Connection and system status monitoring
- **📋 Command History**: Recent voice command logging

### Mobile Compatibility

#### iOS Safari Optimization
```javascript
// Audio format prioritization for iOS
const supportedTypes = [
    'audio/mp4',                  // iOS Safari REQUIRED
    'audio/mp4;codecs=mp4a.40.2', // iOS Safari with codec
    'audio/webm;codecs=opus',     // Android/Desktop
    'audio/wav'                   // Desktop fallback
];
```

#### Android Chrome Support
```javascript
// Audio constraints for Android
const audioConstraints = {
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true,
    channelCount: 1
};
```

## Error Handling

### Common Issues and Solutions

1. **Audio Recording Fails**
   ```javascript
   // Check microphone permissions
   navigator.mediaDevices.getUserMedia({ audio: true })
   ```

2. **Transcription Errors**
   ```python
   # Fallback for failed transcription
   if transcription == "TRANSCRIPTION_FAILED":
       return error_response_with_audio()
   ```

3. **iOS Audio Playback Issues**
   ```javascript
   // Require user interaction for iOS audio
   if (isIOS) {
       showPlayButton(audioUrl);
   }
   ```

### Error Response Format

```json
{
  "success": false,
  "transcription": "Audio processing failed",
  "error_message": "तकनीकी समस्या के कारण आवाज़ नहीं समझ पाए।",
  "audio_content": "base64_error_audio"
}
```

## Performance Optimization

### Server Optimization

```python
# Enable async processing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Audio Processing Optimization

```javascript
// Client-side audio conversion for better compatibility
async function convertToWav(audioBlob) {
    const audioContext = new AudioContext({ sampleRate: 16000 });
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    return audioBufferToWav(audioBuffer);
}
```

## Deployment

### Production Deployment

1. **Use Production ASGI Server**
   ```bash
   pip install gunicorn
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:7860
   ```

2. **Environment Variables**
   ```bash
   export SERVER_URL=https://production-gemma-server.com/
   export GOOGLE_TEXT_TO_SPEECH=prod_api_key
   export PORT=7860
   ```

3. **SSL/HTTPS Setup** (required for audio recording)
   ```bash
   # Use reverse proxy (nginx) or direct SSL
   uvicorn main:app --host 0.0.0.0 --port 7860 --ssl-keyfile key.pem --ssl-certfile cert.pem
   ```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
```

## Monitoring and Logging

### Health Checks

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "voice-server",
        "gemma_server": check_gemma_connection(),
        "tts_service": check_tts_availability()
    }
```

### Performance Metrics

Monitor these key metrics:
- Voice command success rate
- Audio transcription latency
- TTS response time
- Database query performance

## Security Considerations

1. **Audio Data**: Audio files are processed in memory and not stored
2. **API Rate Limiting**: Implement rate limiting for production
3. **CORS Policy**: Configure appropriate CORS settings
4. **HTTPS Required**: Audio recording requires secure contexts

## Troubleshooting

### Common Issues

1. **"Microphone access denied"**
   - Ensure HTTPS is enabled
   - Check browser permissions
   - Verify SSL certificate

2. **"Transcription failed"**
   - Check Gemma server connectivity
   - Verify SERVER_URL in .env
   - Test with smaller audio files

3. **"No audio playback on iPhone"**
   - Ensure phone is not in silent mode
   - Check volume settings
   - Use user-triggered audio playback

4. **"Zone data not found"**
   - Verify sessions_data.csv exists
   - Check CSV column names
   - Ensure zone names match exactly

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Add debug prints in utils.py
print(f"📤 Sending audio data ({len(audio_bytes)} bytes)")
print(f"✅ Transcription: {transcription}")
```

## Contributing

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd voice-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run development server
python main.py
```

### Code Structure

```
voice-server/
├── main.py              # FastAPI application and routes
├── routes.py            # Voice command endpoint
├── utils.py             # Audio processing utilities
├── static/              # Frontend files
│   ├── index.html       # Voice interface
│   ├── app.js           # JavaScript functionality
│   └── style.css        # Cyberpunk styling
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
└── README.md           # This file
```

## License

This project is part of the Gemma Kavach suite. Please refer to the main project license for usage terms.

## Support

For voice server specific issues:
1. Check the troubleshooting section above
2. Verify Gemma 3n server connectivity
3. Test audio recording in browser console
4. Monitor server logs for detailed error messages

---

**Note**: This voice command server is optimized for Indian security scenarios and supports Hindi-English voice interactions. For other languages or domains, modify the transcription prompts and TTS configuration accordingly.