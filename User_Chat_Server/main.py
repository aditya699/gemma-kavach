# main.py - Complete emergency classification server with static files
import os

# AGGRESSIVE compilation disable BEFORE any imports
os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
os.environ["TORCH_USE_CUDA_DSA"] = "1"

import torch

# Disable all torch compilation
torch._dynamo.config.disable = True
torch._dynamo.config.suppress_errors = True
torch.backends.cudnn.benchmark = False
torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32 = False

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from routes import router
from utils import load_model

# Initialize FastAPI app
app = FastAPI(
    title="Emergency Classification API",
    description="AI-powered emergency classification and reporting system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Setup static files (like your vision server)
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# Create static directory if it doesn't exist
STATIC_DIR.mkdir(exist_ok=True)

# Mount static files - serve emergency report form
app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)

# Add redirect from root to emergency form
from fastapi.responses import RedirectResponse

@app.get("/emergency")
async def emergency_form():
    """Redirect to the emergency report form"""
    return RedirectResponse(url="/static/index.html")

@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    print("🚀 Starting Emergency Classification Server...")
    print("📊 Loading fine-tuned emergency classification model...")
    
    success = load_model()
    if success:
        print("✅ Model loaded successfully!")
    else:
        print("❌ Model loading failed!")
    
    print("🌐 Server running on http://localhost:8501")
    print("📋 Emergency Report Form: http://localhost:8501/static/index.html")
    print("🔍 API Classification: POST http://localhost:8501/ask_class")
    print("📧 Emergency Reports: POST http://localhost:8501/emergency/report")

@app.get("/")
async def root():
    """Redirect to the emergency report form"""
    return RedirectResponse(url="/static/index.html")

@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "message": "Emergency Classification API - Gemma Kavach",
        "status": "running",
        "features": {
            "ai_classification": "6 emergency categories supported",
            "emergency_reports": "Image + email alerts enabled",
            "web_interface": "Cyberpunk-styled emergency form"
        },
        "endpoints": {
            "classify": "POST /ask_class",
            "emergency_report": "POST /emergency/report", 
            "emergency_form": "GET /static/index.html",
            "model_info": "GET /model_info",
            "health": "GET /health",
            "debug": "GET /debug"
        },
        "categories": [
            "child_lost",
            "crowd_panic", 
            "lost_item",
            "medical_help",
            "need_interpreter",
            "small_fire"
        ]
    }

@app.get("/health")
async def health_check():
    from utils import model
    return {
        "status": "healthy", 
        "model_loaded": model is not None,
        "service": "emergency-classification",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    print("🔥 Gemma Kavach Emergency Classification System")
    print("=" * 50)
    print("🧠 AI Model: Gemma 3N 2B + LoRA Fine-tuning")
    print("📱 Web Interface: Cyberpunk Emergency Report Form") 
    print("📧 Email Alerts: Automatic emergency notifications")
    print("☁️ Cloud Storage: GCS image backup")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8501,
        reload=True,
        log_level="info"
    )