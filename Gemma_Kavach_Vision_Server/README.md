# Gemma Kavach Vision Server

A real-time crowd safety monitoring system that provides dual-analysis capabilities for crowd density assessment and motion behavior detection. Built with FastAPI and powered by Gemma AI for intelligent video analytics.

## 🎯 Overview

Gemma Kavach Vision is an advanced crowd monitoring solution designed for real-time safety assessment in crowded environments like festivals, events, and public gatherings. The system performs dual analysis on video frames to detect:

- **Crowd Density**: Analyzes how tightly packed people are (Low/Medium/High)
- **Motion Behavior**: Detects panic or chaotic movement patterns (Calm/Chaotic)
- **Risk Assessment**: Calculates sophisticated risk scores based on combined analysis
- **Alert System**: Automated email alerts for critical situations

## 🚀 Features

### Core Functionality
- **Real-time Video Analysis**: Processes camera feeds frame by frame
- **Dual Analysis Engine**: Simultaneous crowd density and motion analysis
- **Risk Scoring**: Sophisticated algorithm considering multiple factors
- **Session Management**: Track monitoring sessions with detailed analytics
- **Cloud Storage**: Google Cloud Storage integration for data persistence
- **Email Alerts**: Automated notifications for critical situations

### Web Interface
- **Live Camera Feed**: Real-time video display with analysis overlay
- **Risk Meter**: Visual risk assessment with color-coded indicators
- **Analytics Dashboard**: Comprehensive statistics and breakdowns
- **Session Controls**: Start/stop monitoring with location tracking
- **Activity Log**: Real-time event logging and analysis history

### API Endpoints
- `POST /api/session/create` - Create new monitoring session
- `POST /api/session/{session_id}/frame` - Analyze individual frames
- `GET /api/session/{session_id}` - Get session status and analytics
- `GET /api/monitoring/status` - System health check

## 📋 Prerequisites

- Python 3.8+
- Google Cloud Storage account and credentials
- Email account with app password for alerts
- Camera/webcam for video input

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Gemma_Kavach_Vision_Server
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Google Cloud Storage**
   - Create a GCS bucket
   - Download service account key as `gcs_key.json`
   - Place the key file in the project root

4. **Configure environment variables**
   Create a `.env` file with:
   ```env
   BUCKET_NAME=your-gcs-bucket-name
   GOOGLE_APP_PASSWORD=your-email-app-password
   ```

## 🏃 Usage

### Starting the Server

```bash
python main.py
```

The server will start on `http://localhost:38277`

### Web Interface

1. Open your browser and navigate to `http://localhost:38277`
2. Configure location and operator details
3. Click "Start Monitoring" to begin analysis
4. Monitor real-time risk assessment and analytics

### API Usage

**Create a monitoring session:**
```bash
curl -X POST "http://localhost:38277/api/session/create" \
     -H "Content-Type: application/json" \
     -d '{"location": "Event Hall A", "operator_name": "Security Team"}'
```

**Analyze a frame:**
```bash
curl -X POST "http://localhost:38277/api/session/{session_id}/frame" \
     -F "frame=@image.jpg"
```

## 🧠 Analysis Engine

### Crowd Density Analysis
The system evaluates crowd density using visual analysis:
- **Low**: Sparse crowd with plenty of personal space
- **Medium**: Moderate crowding with some personal space
- **High**: Dense crowd with minimal space between people

### Motion Behavior Analysis
Detects panic and chaotic behavior patterns:
- **Calm**: Normal, organized movement patterns
- **Chaotic**: Signs of panic, running, pushing, or distress

### Risk Assessment Matrix
| Density | Motion | Risk Level |
|---------|--------|------------|
| High | Chaotic | CRITICAL |
| Medium | Chaotic | HIGH |
| Low | Chaotic | MODERATE |
| High | Calm | MODERATE |
| Medium/Low | Calm | SAFE |

## 📊 Risk Scoring Algorithm

The system calculates risk scores using:
- **Weighted Analysis**: Different risk levels have different weights (CRITICAL=100, HIGH=60, MODERATE=25, SAFE=0)
- **Pattern Recognition**: Penalties for concerning patterns (>30% high density, >20% chaotic motion)
- **Trend Analysis**: Considers rapid escalation patterns
- **Historical Context**: Analyzes session-wide trends

## 🚨 Alert System

Automated alerts are triggered when:
- Risk score exceeds 70%
- 2+ CRITICAL frames detected
- Rapid escalation patterns identified
- Consecutive flagged frames indicate emergency

Alert emails include:
- Detailed analysis breakdown
- Risk level statistics
- Crowd density and motion analysis
- Session information and timestamps

## 🏗️ Architecture

```
Gemma_Kavach_Vision_Server/
├── main.py              # FastAPI application entry point
├── routes.py            # API endpoints and request handling
├── utils.py             # Core utilities and analysis functions
├── static/              # Web interface files
│   ├── index.html       # Main dashboard
│   ├── style.css        # Styling
│   └── app.js           # Frontend JavaScript
├── gcs_key.json         # Google Cloud credentials
└── requirements.txt     # Python dependencies
```

## 🔧 Configuration

### Server Settings
- **Host**: `0.0.0.0` (all interfaces)
- **Port**: `38277`
- **Reload**: Enabled for development

### Analysis Parameters
- **Minimum frames for alert**: 5
- **Risk threshold**: 70%
- **Critical frames threshold**: 2

### Cloud Storage
- **Sessions**: Stored in `sessions/` prefix
- **Flagged frames**: Stored in `flagged_frames/` prefix
- **Retention**: Configurable per GCS bucket settings

## 📈 Monitoring and Analytics

The system provides comprehensive analytics:
- **Real-time metrics**: Current analysis results
- **Session statistics**: Frames analyzed, flagged, and critical counts
- **Distribution charts**: Density, motion, and risk level breakdowns
- **Time-series data**: Risk score trends over time
- **Alert history**: Triggered alerts and responses

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the activity log in the web interface
- Review server logs for error messages
- Verify GCS connectivity and credentials
- Ensure camera permissions are granted

## 🔄 Version History

- **v1.0.0**: Initial release with dual-analysis capabilities
- Enhanced risk scoring algorithm
- Real-time web interface
- Cloud storage integration
- Email alert system
