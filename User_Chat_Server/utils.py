# utils.py
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

import unsloth  # Import unsloth first to avoid warnings
from transformers import AutoTokenizer, BitsAndBytesConfig, AutoModelForCausalLM
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for model and tokenizer
model = None
tokenizer = None

# Categories
CATEGORIES = ["child_lost", "crowd_panic", "lost_item", "medical_help", "need_interpreter", "small_fire"]
CATEGORIES_STR = ", ".join(CATEGORIES)

def load_model():
    """Load fine-tuned model with LoRA - NO FALLBACKS!"""
    global model, tokenizer
    
    try:
        logger.info("Loading base model + LoRA adapter (GPU only)...")
        
        from unsloth import FastModel
        
        # Load base model directly on GPU
        model, tokenizer = FastModel.from_pretrained(
            "unsloth/gemma-3n-E2B-it",
            load_in_4bit=True,
            dtype=torch.bfloat16,
        )
        
        # Load your LoRA adapter from FineTunedModel - THIS MUST WORK!
        model.load_adapter("../FineTunedModel", adapter_name="emergency")
        
        # Ensure tokenizer has pad token
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            
        logger.info("✅ Fine-tuned model with LoRA loaded successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Fine-tuned model loading FAILED: {e}")
        logger.error("❌ NO FALLBACKS - Fix the LoRA loading issue!")
        
        # Reset globals to None
        model = None
        tokenizer = None
        return False

def classify_emergency(text: str) -> str:
    """Classify emergency text - Using RAW tokenizer approach like working Gemma server"""
    global model, tokenizer
    
    if model is None or tokenizer is None:
        raise RuntimeError("Model not loaded")
    
    try:
        logger.info(f"Classifying text: '{text}'")
        
        # Create prompt exactly like training
        prompt = f"Classify this emergency into one of these categories: {CATEGORIES_STR}\n\nEmergency: {text}\n\nCategory:"
        
        # Use RAW tokenizer approach (like your working Gemma server)
        messages = [{
            "role": "user",
            "content": [{"type": "text", "text": prompt}]
        }]
        
        # Apply chat template using RAW tokenizer (WORKING approach)
        inputs = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(model.device)
        
        logger.info(f"Tokenization successful, shape: {inputs['input_ids'].shape}")
        
        # Generate with same params as your working server
        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=5,
                do_sample=False,  # Greedy for consistent results
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        
        logger.info(f"Generation successful, shape: {outputs.shape}")
        
        # Decode response - same as working server
        response = tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[-1]:], 
            skip_special_tokens=True
        ).strip()
        
        logger.info(f"Raw response: '{response}'")
        
        # Extract category - same logic as test.py
        response_lower = response.lower()
        for category in CATEGORIES:
            if category in response_lower:
                logger.info(f"Found category: {category}")
                return category
        
        # Fallback
        fallback = response_lower.split()[0] if response_lower else "unknown"
        logger.info(f"Using fallback: {fallback}")
        return fallback
        
    except Exception as e:
        logger.error(f"Classification error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return "error"

def get_model_info():
    """Get model information"""
    return {
        "model_loaded": model is not None,
        "categories": CATEGORIES,
        "model_path": "../FineTunedModel (LoRA)",
        "device": str(model.device) if model else "not_loaded"
    }