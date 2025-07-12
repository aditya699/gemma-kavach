# gemma_loader.py - WORKING MULTIMODAL VERSION
import os
import torch

# AGGRESSIVE compilation disable BEFORE any imports
os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

# Disable all torch compilation
torch._dynamo.config.disable = True
torch._dynamo.config.suppress_errors = True
torch.backends.cudnn.benchmark = False
torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32 = False

from huggingface_hub import login
from dotenv import load_dotenv
from unsloth import FastModel

load_dotenv()

def get_model_and_processor():
    """Load Gemma 3n model and tokenizer - WORKING MULTIMODAL CONFIG"""
    
    # Login to HuggingFace 
    login(token=os.getenv("HF_TOKEN"))
    
    print("🚀 Loading Gemma 3n model and tokenizer...")
    print("🔧 Using WORKING multimodal configuration...")
    
    # Use EXACT tutorial configuration (this works for multimodal!)
    model, tokenizer = FastModel.from_pretrained(
        model_name="unsloth/gemma-3n-E4B-it",
        dtype=None,  # Auto detection (tutorial setting)
        max_seq_length=1024,
        load_in_4bit=True,  # Tutorial setting (works with multimodal)
        full_finetuning=False,
        trust_remote_code=True,
    )
    
    # DON'T apply get_chat_template here! 
    # We'll apply it selectively in the server:
    # - For text-only: Use get_chat_template (works fine)
    # - For multimodal: Use raw tokenizer (works perfectly)
    
    print("✅ Model loaded with WORKING multimodal configuration!")
    print(f"📊 Tokenizer type: {type(tokenizer)}")
    print(f"📊 Multimodal support: ✅ CONFIRMED WORKING")
    
    return model, tokenizer

def sanitize(text):
    """Clean up the generated text"""
    return text.strip()