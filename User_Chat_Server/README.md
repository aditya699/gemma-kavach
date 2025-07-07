# Gemma Kavach - Emergency Classification System

A modern AI-powered emergency classification system with a beautiful web interface. This server classifies emergency text descriptions into predefined categories using fine-tuned machine learning models.

## 🚀 Features

### Web Interface
- **Modern UI**: Beautiful, responsive design with blue gradient theme
- **Real-time Classification**: Instant emergency text classification
- **Quick Examples**: Pre-built example texts for each emergency category
- **Live Statistics**: Session tracking with response times and success rates
- **Classification History**: Recent classifications with timestamps
- **Model Information**: Real-time model status and device information

### API Endpoints
- `POST /ask_class` - Classify emergency text
- `GET /model_info` - Get model status and information
- `GET /health` - Health check endpoint
- `GET /debug` - Debug information

## 📋 Supported Emergency Categories

1. **Child Lost** - Missing children scenarios
2. **Crowd Panic** - Crowd control and panic situations
3. **Medical Help** - Medical emergencies and assistance needed
4. **Small Fire** - Fire incidents requiring attention
5. **Lost Item** - Lost personal belongings
6. **Need Interpreter** - Language barrier assistance

## 🖥️ Web Interface

### Main Features
- **Text Input**: Large textarea for emergency descriptions (500 char limit)
- **Character Counter**: Real-time character count with color coding
- **Example Buttons**: Quick-fill examples for each category
- **Classification Result**: Prominent display of AI classification result
- **Session Statistics**: Live tracking of classifications and performance
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile

### Keyboard Shortcuts
- `Ctrl + Enter`: Classify current text
- `Ctrl + L`: Clear text input
- `Escape`: Close modals

## 🎨 Design Theme

The interface features a modern, professional design with:
- **Color Scheme**: Blue gradient theme (#3b82f6, #8b5cf6, #06b6d4)
- **Typography**: Inter font family for optimal readability
- **Animations**: Smooth transitions and hover effects
- **Responsive**: Mobile-first design approach
- **Accessibility**: High contrast and keyboard navigation support

## 🚀 Quick Start

1. **Start the Server**:
   ```bash
   cd User_Chat_Server
   python main.py
   ```

2. **Access Web Interface**:
   - Open browser to `http://localhost:8501`
   - Start classifying emergency texts immediately

3. **API Usage**:
   ```python
   import requests
   
   response = requests.post('http://localhost:8501/ask_class', 
                          json={'text': 'A child is missing near the main stage'})
   print(response.json())  # {'category': 'child_lost'}
   ```

## 📊 Session Statistics

The web interface tracks:
- **Total Classifications**: Number of texts classified
- **Average Response Time**: API response performance
- **Success Rate**: Classification success percentage
- **Session Time**: Time since interface was opened

## 🔧 Technical Details

### Frontend Stack
- **HTML5**: Semantic markup with accessibility features
- **CSS3**: Modern styling with animations and responsive design
- **JavaScript ES6+**: Class-based architecture with async/await
- **Font Awesome**: Icon library for enhanced UI

### Backend Integration
- **FastAPI**: Python web framework
- **Gemma Models**: Fine-tuned for emergency classification
- **Static File Serving**: Integrated web interface serving

## 🎯 Example Texts

### Child Lost
"A child is missing near the main stage area"

### Crowd Panic
"People are running and pushing in panic near the exit"

### Medical Help
"Someone needs medical assistance, they collapsed"

### Small Fire
"There's a small fire in the food court trash bin"

### Lost Item
"I lost my wallet and phone near the entrance"

### Need Interpreter
"Need a translator for someone who doesn't speak the local language"

## 📱 Mobile Support

The interface is fully responsive and optimized for mobile devices with:
- Touch-friendly buttons and inputs
- Responsive grid layouts
- Mobile-optimized typography
- Gesture support for navigation

## 🔒 Security Features

- Input validation and sanitization
- Character limits to prevent abuse
- Error handling for API failures
- CORS protection for secure communication

---

## 🤝 Integration with Gemma Kavach Vision Server

This Emergency Classification System works alongside the Gemma Kavach Vision Server to provide comprehensive crowd safety monitoring:

- **Vision Server**: Real-time crowd analysis and risk assessment
- **Chat Server**: Emergency text classification and response
- **Combined Solution**: Complete safety monitoring ecosystem

Both servers feature modern web interfaces with consistent design patterns and can be deployed together for comprehensive emergency management systems.

---

**Built with ❤️ for emergency response and crowd safety management.**