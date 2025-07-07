# main.py
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
from routes import router
from utils import load_model

# Initialize FastAPI app
app = FastAPI(
    title="Emergency Classification API",
    description="API for classifying emergency situations",
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

# Include routes
app.include_router(router)

@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    print("🚀 Starting Emergency Classification Server...")
    load_model()
    print("✅ Model loaded successfully!")
    print("🌐 Server running on http://localhost:8501")

@app.get("/")
async def root():
    return {
        "message": "Emergency Classification API",
        "status": "running",
        "endpoints": {
            "classify": "POST /ask_class",
            "health": "GET /health"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": True}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8501,
        reload=True,
        log_level="info"
    )