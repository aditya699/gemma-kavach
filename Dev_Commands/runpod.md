# RunPod Deployment Commands

## Environment Setup

### Initial Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Complete Environment Setup
```bash
# One-liner for complete setup
cd workspace && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

## Server Deployment

### Gemma Server
```bash
# Start Gemma 3n FastAPI server (Port 8000)
python gemma_server.py

# Alternative with workspace navigation
cd workspace && source venv/bin/activate && cd GemmaServer && python gemma_server.py
```

### Vision Server
```bash
# Start Gemma Kavach Vision Server (Port 38277)
uvicorn main:app --host 0.0.0.0 --port 38277 --reload

# With workspace navigation
cd workspace && source venv/bin/activate && cd Gemma_Kavach_Vision_Server && uvicorn main:app --host 0.0.0.0 --port 38277 --reload
```

### Voice Server
```bash
# Start Gemma Kavach Voice Server (Port 7860)
cd workspace && source venv/bin/activate && cd Gemma_Kavach_Voice_Server && uvicorn main:app --host 0.0.0.0 --port 7860 --reload
```

### Generic Server Commands
```bash
# Alternative port configurations
uvicorn main:app --host 0.0.0.0 --port 8081 --reload
```

## Process Management

### Background Jobs
```bash
# Run job in background with logging
nohup python job.py >> train.log 2>&1 &

# Check if job is running
ps aux | grep job.py

# Monitor logs in real-time
tail -f train.log
```

## Maintenance Commands

### Force Delete
```bash
# Force delete directory (use with caution)
rm -rf Gemma_Kavach_Voice_Server
```

## Port Configuration

| Service | Port | Command |
|---------|------|---------|
| Gemma FastAPI | 8000 | `python gemma_server.py` |
| Generic Server | 8081 | `uvicorn main:app --host 0.0.0.0 --port 8081 --reload` |
| Vision Server | 38277 | `uvicorn main:app --host 0.0.0.0 --port 38277 --reload` |
| Voice Server | 7860 | `uvicorn main:app --host 0.0.0.0 --port 7860 --reload` |

## Quick Reference

### Environment Activation
```bash
source venv/bin/activate
```

### Server Health Check
```bash
# Check running processes
ps aux | grep python
ps aux | grep uvicorn

# Check port usage
netstat -tlnp | grep :8000
netstat -tlnp | grep :38277
netstat -tlnp | grep :7860
```

### Troubleshooting
```bash
# Kill process by port
sudo kill -9 $(sudo lsof -t -i:8000)

# Check logs
tail -f train.log
journalctl -u your-service-name -f
```

## Notes

- Always activate the virtual environment before running commands
- Use `--reload` flag for development environments
- Monitor logs regularly for debugging
- Ensure proper port configurations to avoid conflicts
- Use `nohup` for long-running background processes

tail -f voice_server.log
tail -f vision_server.log
tail -f gemma_server.log
tail -f main_app.log