"""
FastAPI wrapper for Gemma-3n model.

• POST /generate      – text→text 
• POST /ask_image     – image+prompt→text
• POST /ask          – audio→text

"""

import base64, os, tempfile, torch
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from gemma_loader import get_model_and_processor, sanitize

# --------------------------------------------------------------------
# Request Models
# --------------------------------------------------------------------

class TextRequest(BaseModel):
    prompt: str
    max_tokens: int = 100

class AudioPayload(BaseModel):
    data: str  # base-64 audio data

# --------------------------------------------------------------------
# FastAPI + CORS
# --------------------------------------------------------------------

app = FastAPI(title="Gemma 3n Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Open for now, can restrict later
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------
# Load model/processor once
# --------------------------------------------------------------------

model, processor = get_model_and_processor()

# --------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------

@app.get("/")
async def root():
    return {"message": "Gemma 3n Server is running!", "status": "ready"}

@app.post("/generate")
async def generate_text(request: TextRequest):
    """Text generation endpoint"""
    try:
        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are a helpful assistant."}],
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": request.prompt}],
            },
        ]

        inputs = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(model.device, dtype=model.dtype)

        with torch.inference_mode():
            out = model.generate(**inputs, max_new_tokens=request.max_tokens, disable_compile=True)

        reply = processor.decode(
            out[0][inputs["input_ids"].shape[-1] :], skip_special_tokens=True
        )
        return {"text": sanitize(reply)}

    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc

@app.post("/ask_image")
async def ask_image(
    prompt: str = Form(...),
    image: UploadFile = File(...),
):
    """Image + text processing endpoint"""
    img_path = None
    try:
        suffix = os.path.splitext(image.filename)[1] or ".png"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            img_path = tmp.name
            tmp.write(await image.read())

        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are a helpful assistant."}],
            },
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": img_path},
                    {"type": "text", "text": prompt},
                ],
            },
        ]

        inputs = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(model.device, dtype=model.dtype)

        with torch.inference_mode():
            out = model.generate(**inputs, max_new_tokens=256, disable_compile=True)

        reply = processor.decode(
            out[0][inputs["input_ids"].shape[-1] :], skip_special_tokens=True
        )
        return {"text": sanitize(reply)}

    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc
    finally:
        if img_path and os.path.exists(img_path):
            os.remove(img_path)

@app.post("/ask")
async def ask_audio(payload: AudioPayload):
    """Audio processing endpoint"""
    wav_path = None
    try:
        # Decode base64 audio data
        wav_bytes = base64.b64decode(payload.data)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            wav_path = tmp.name
            tmp.write(wav_bytes)

        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are a helpful assistant."}],
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Here is my audio message:"},
                    {"type": "audio", "audio": wav_path},
                ],
            },
        ]

        inputs = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(model.device, dtype=model.dtype)

        with torch.inference_mode():
            out = model.generate(**inputs, max_new_tokens=256, disable_compile=True)

        reply = processor.decode(
            out[0][inputs["input_ids"].shape[-1] :], skip_special_tokens=True
        )
        return {"text": sanitize(reply)}

    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc
    finally:
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)