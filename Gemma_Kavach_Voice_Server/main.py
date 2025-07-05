# main.py - Your existing main.py file (no changes needed)
# Just make sure these imports work for the new voice command functions

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routes import router  # This will now include the voice command endpoint

# Your existing FastAPI setup code remains the same
# The new endpoint will be available at: /api/voice-command

app = FastAPI(
    title="Gemma Kavach Vision Server",
    description="Crowd Safety Monitoring API with Voice Commands",  # Updated description
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include monitoring routes (now includes voice command)
app.include_router(router, prefix="/api")

from pathlib import Path

BASE_DIR   = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount(
    "/",
    StaticFiles(directory=STATIC_DIR, html=True),
    name="static"
)

@app.get("/")
async def root():
    return {
        "message": "Gemma Kavach Vision Server is running!",
        "status": "ready",
        "server": "crowd-monitoring-backend",
        "new_feature": "Voice command endpoint available at /api/voice-command"  # Added this
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "vision-server"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Gemma Kavach Vision Server...")
    print("📍 Server will run on: http://localhost:7860")
    print("📖 API docs will be available at: http://localhost:7860/docs")
    print("🎤 Voice command endpoint: http://localhost:7860/api/voice-command")  # Added this
    
    uvicorn.run(
        app, 
        host="0.0.0.0",
        port=7860,
        reload=True
    )