# main.py - Gemma Kavach Vision Server
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routes import router  # Import our routes

# Create FastAPI app
app = FastAPI(
    title="Gemma Kavach Vision Server",
    description="Crowd Safety Monitoring API",
    version="1.0.0"
)

# Add CORS middleware (allows frontend to call this API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include monitoring routes
app.include_router(router, prefix="/api")  # All routes will be /api/v1/...

from pathlib import Path

BASE_DIR   = Path(__file__).resolve().parent        # folder where main.py lives
STATIC_DIR = BASE_DIR / "static"                    # …/static (absolute path)

# Serve static files (frontend)
app.mount(
    "/",                  # leave it on root
    StaticFiles(directory=STATIC_DIR, html=True),
    name="static"
)

# Basic test endpoint
@app.get("/")
async def root():
    return {
        "message": "Gemma Kavach Vision Server is running!",
        "status": "ready",
        "server": "crowd-monitoring-backend"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "vision-server"}

# Run the server
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Gemma Kavach Vision Server...")
    print("📍 Server will run on: http://localhost:38277")
    print("📖 API docs will be available at: http://localhost:38277/docs")
    
    uvicorn.run(
        app, 
        host="0.0.0.0",  # Listen on all interfaces
        port=38277,       # Using 38277 instead of 8080 (Windows permission issue)
        reload=True      # Auto-reload when code changes
    )