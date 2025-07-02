# gemma_loader.py
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
from huggingface_hub import login
import os
from dotenv import load_dotenv
load_dotenv()

def get_model_and_processor():
    """Load Gemma 3n model and processor for multimodal support"""
    
    # Login to HuggingFace 
    login(token=os.getenv("HF_TOKEN"))
    
    print("🚀 Loading Gemma 3n model and processor...")
    
    # Suppress compilation issues
    torch._dynamo.config.suppress_errors = True
    
    # Use Google's official approach for audio support
    GEMMA_MODEL_ID = "google/gemma-3n-E4B-it" #This is a 8 billion parameter model
    
    processor = AutoProcessor.from_pretrained(GEMMA_MODEL_ID)
    model = AutoModelForImageTextToText.from_pretrained(
        GEMMA_MODEL_ID, 
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    
    print("✅ Model loaded successfully with audio support")
    return model, processor

def sanitize(text):
    """Clean up the generated text"""
    return text.strip()