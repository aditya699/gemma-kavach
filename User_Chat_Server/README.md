# Emergency Reporting Application - Gemma Kavach

## Overview

The Emergency Reporting Application is a citizen-facing component of the Gemma Kavach crowd safety suite that enables real-time emergency reporting with AI-powered classification. Users can submit emergency situations through a cyberpunk-styled web interface, and the system automatically classifies the emergency type and sends alerts to response teams.

## Features

- **🧠 AI Classification**: Automatic emergency categorization using fine-tuned Gemma 3n 2B model
- **📱 Mobile-First Design**: Responsive cyberpunk interface optimized for smartphones
- **📷 Image Upload**: File upload and camera capture for emergency photo documentation
- **📧 Email Alerts**: Automated email notifications to emergency response teams
- **☁️ Cloud Storage**: Google Cloud Storage for image backup and retrieval
- **🔒 Form Validation**: Client-side validation and server-side verification

## Emergency Categories

The AI system classifies emergencies into 6 categories:

1. **🚨 Child Lost** - Missing children reports (Priority: CRITICAL)
2. **👥 Crowd Panic** - Stampede/panic situations (Priority: CRITICAL)
3. **🏥 Medical Help** - Medical emergencies (Priority: HIGH)
4. **🔥 Small Fire** - Fire incidents (Priority: HIGH)
5. **🗣️ Need Interpreter** - Language assistance (Priority: MEDIUM)
6. **📦 Lost Item** - Lost belongings (Priority: LOW)

## System Architecture

```
User Report Flow:
Form Input → AI Classification → Image Upload → Email Alert → Response Team Notification
```

### Core Components

1. **Frontend** (`index.html` + `app.js` + `style.css`) - User interface
2. **Backend API** (`main.py` + `routes.py`) - Classification and processing
3. **AI Model** (`utils.py`) - Fine-tuned emergency classification
4. **Email System** - Automated alert generation
5. **Cloud Storage** - Image backup and retrieval

## Requirements

### Server Requirements
- **Python**: 3.9+
- **GPU**: RTX 4090 or equivalent (for AI model)
- **RAM**: 16GB+ recommended

### Dependencies

```bash
# Core server dependencies
pip install fastapi uvicorn python-multipart
pip install transformers torch unsloth
pip install pandas python-dotenv

# Emergency reporting features
pip install google-cloud-storage
```

### External Services

1. **Google Cloud Storage** - Image storage and backup
2. **Gmail SMTP** - Email alert system
3. **Gemma 3n Model** - Fine-tuned emergency classification

## Quick Start

### Step 1: Environment Setup

Create a `.env` file:
```bash
# Email Configuration (Gmail SMTP)
GOOGLE_APP_PASSWORD=your_gmail_app_password

# Google Cloud Storage
BUCKET_NAME=your-gcs-bucket-name

# Server Configuration
HOST=0.0.0.0
PORT=8501
```

### Step 2: Model Setup

Ensure your fine-tuned model is available:
```bash
# Fine-tuned model should be in ../FineTunedModel/
ls ../FineTunedModel/
# Should contain: adapter_config.json, adapter_model.safetensors, etc.
```

### Step 3: Start the Server

```bash
# Start the emergency reporting server
python main.py
```

Server will be available at:
- **Emergency Report Form**: http://localhost:8501/
- **API Classification**: http://localhost:8501/ask_class
- **API Documentation**: http://localhost:8501/docs
- **Health Check**: http://localhost:8501/health

### Step 4: Access the Application

1. Open http://localhost:8501 in your browser
2. Fill out the emergency report form
3. Upload an emergency photo
4. Submit and receive AI classification
5. Response team gets automated email alert

## API Endpoints

### Emergency Classification

**POST** `/ask_class`

Classifies emergency text into predefined categories.

**Request:**
```json
{
  "text": "Bacha kho gaya hai zone me"
}
```

**Response:**
```json
{
  "category": "child_lost"
}
```

### Emergency Report Submission

**POST** `/emergency/report`

Submits complete emergency report with image and sends alerts.

**Request (multipart/form-data):**
```http
POST /emergency/report
Content-Type: multipart/form-data

location: "Sector 17 Plaza"
message: "Child missing near food court"
classification: "child_lost"
contact: "+91-9876543210"
reportId: "EMG-123456-ABC"
image: [image file]
```

**Response:**
```json
{
  "status": "success",
  "report_id": "EMG-123456-ABC",
  "message": "Emergency report submitted and alert sent",
  "image_saved": true,
  "timestamp": "2025-07-09 14:30:00"
}
```

### System Status

**GET** `/health`

Returns system health and model status.

```json
{
  "status": "healthy",
  "model_loaded": true,
  "service": "emergency-classification",
  "version": "1.0.0"
}
```

### Batch Classification

**POST** `/batch_classify`

Classifies multiple texts at once.

**Request:**
```json
[
  {"text": "Bacha kho gaya hai"},
  {"text": "Medical emergency"}
]
```

### Debug Information

**GET** `/debug`

Returns model loading and status information.

## User Interface Features

### Emergency Report Form

- **📍 Location Input**: Manual entry of emergency location
- **📝 Description Field**: Multilingual emergency description (Hindi/English)
- **📷 Photo Upload**: File upload with drag-and-drop and camera capture support
- **📞 Contact Info**: Optional contact number for follow-up

### Real-time Processing

- **⚡ Form Validation**: Client-side input validation
- **🧠 AI Analysis**: Real-time emergency classification
- **📧 Alert Status**: Step-by-step processing visualization with animated loading
- **✅ Confirmation**: Success confirmation with report ID

### Mobile Optimization

- **📱 Touch-Friendly**: Large buttons and touch targets
- **📷 Camera Integration**: Direct camera access on mobile devices using `capture="environment"`
- **🔄 Drag & Drop**: File upload with drag and drop support
- **💨 Responsive Design**: Optimized for all screen sizes

## Configuration

### Email Alert System

Configure Gmail SMTP in `utils.py`:
```python
# Email Configuration
EMAIL_SENDER = "ab0358031@gmail.com"
EMAIL_PASSWORD = os.getenv("GOOGLE_APP_PASSWORD")
EMAIL_RECEIVER = "ab0358031@gmail.com"

def send_emergency_email(report_data: dict):
    # Email composition with emergency details
    # Includes: location, classification, image, priority level
```

### Cloud Storage Setup

Configure Google Cloud Storage in `utils.py`:
```python
EMERGENCY_BUCKET = os.getenv("BUCKET_NAME", "your-bucket-name")
EMERGENCY_IMAGES_PREFIX = "emergency_reports/"

def save_emergency_image_to_gcs(report_id: str, image_data: bytes, filename: str):
    # Saves images with unique names
    # Format: emergency_reports/{report_id}_{timestamp}.{extension}
```

### AI Model Configuration

Model loading in `utils.py`:
```python
def load_model():
    # Load base Gemma 3n model
    model, tokenizer = FastModel.from_pretrained("unsloth/gemma-3n-E2B-it")
    
    # Load fine-tuned LoRA adapter
    model.load_adapter("../FineTunedModel", adapter_name="emergency")
    
    return True  # Success
```

## Email Alert System

### Alert Content

Emergency emails include:
- **🚨 Subject**: Emergency type and location
- **📍 Location**: User-provided location information
- **🆔 Report ID**: Auto-generated unique tracking identifier
- **🏷️ AI Classification**: Category and description
- **📝 Description**: User-provided emergency details
- **📷 Photo**: Attached emergency image
- **📞 Contact**: Reporter contact information (if provided)
- **⚠️ Priority Level**: Response urgency classification

### Priority Levels

```python
def get_priority_level(classification: str) -> str:
    priority_levels = {
        'child_lost': 'CRITICAL',
        'crowd_panic': 'CRITICAL', 
        'medical_help': 'HIGH',
        'small_fire': 'HIGH',
        'need_interpreter': 'MEDIUM',
        'lost_item': 'LOW'
    }
```

## Frontend Implementation

### Cyberpunk Design System

The interface uses a futuristic cyberpunk aesthetic with:

- **Animated gradients**: Moving background patterns
- **Neon effects**: Glowing borders and text shadows
- **Interactive elements**: Hover and focus animations
- **Loading animations**: Dual spinner rings and step indicators

### Form Validation

```javascript
validateForm() {
    const location = this.elements.locationInput.value.trim();
    const message = this.elements.messageInput.value.trim();
    
    if (!location) {
        this.showToast('Please enter the emergency location', 'error');
        return false;
    }
    
    if (!message) {
        this.showToast('Please describe the emergency situation', 'error');
        return false;
    }
    
    if (!this.selectedImage) {
        this.showToast('Please attach an image of the emergency', 'error');
        return false;
    }
    
    return true;
}
```

### Image Upload Features

- **File validation**: Image type and size checking (10MB max)
- **Preview display**: Immediate image preview with remove option
- **Drag & drop**: Visual feedback during drag operations
- **Camera capture**: Mobile camera integration with `capture="environment"`

## Testing and Development

### Local Development

```bash
# Start development server with auto-reload
python main.py
```

### Testing Classification

```python
import requests

def test_classification(text):
    response = requests.post('http://localhost:8501/ask_class', 
                           json={'text': text})
    return response.json()

# Test cases
test_cases = [
    "Bacha kho gaya hai",
    "Medical emergency help needed", 
    "Fire in building",
    "Lost my wallet",
    "Need translator help",
    "Crowd panic situation"
]

for text in test_cases:
    result = test_classification(text)
    print(f"{text} → {result['category']}")
```

### Browser Compatibility

- **✅ Chrome/Edge**: Full feature support including camera
- **✅ Firefox**: Full feature support  
- **✅ Safari (iOS)**: Camera access with `capture="environment"`
- **✅ Mobile Browsers**: Touch-optimized interface

## File Structure

```
emergency-app/
├── main.py              # FastAPI application and routes
├── routes.py            # API endpoints for classification and reports
├── utils.py             # Model loading and utility functions
├── static/              # Frontend files
│   ├── index.html       # Emergency report form
│   ├── app.js           # JavaScript functionality
│   └── style.css        # Cyberpunk styling
└── .env                 # Environment variables
```

## Troubleshooting

### Common Issues

1. **"Model not loaded"**
   ```bash
   # Check model path exists
   ls ../FineTunedModel/
   # Check GPU memory
   nvidia-smi
   ```

2. **"Email sending failed"**
   ```bash
   # Verify Gmail app password is set
   echo $GOOGLE_APP_PASSWORD
   ```

3. **"Image upload failed"**
   ```bash
   # Check GCS bucket name
   echo $BUCKET_NAME
   # Verify GCS credentials
   ```

4. **"Camera access denied"**
   - Ensure HTTPS is enabled for camera access
   - Check browser permissions

### Debug Mode

Enable detailed logging by checking the server console output:
- Model loading status
- Classification results
- Email sending status
- Image upload progress

## Support

For emergency app specific issues:
1. Check the troubleshooting section above
2. Verify model loading and classification accuracy
3. Test email configuration with Gmail SMTP
4. Monitor browser console for frontend errors
5. Check server logs for backend issues

---

**Note**: This emergency reporting application is optimized for Indian emergency scenarios and supports Hindi-English text. The system requires a fine-tuned Gemma 3n model and proper configuration of email and cloud storage services.