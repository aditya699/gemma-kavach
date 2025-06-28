# test_gemma3n_basic.py
print("🚀 Loading Gemma 3n...")

# Set up Hugging Face authentication first
from huggingface_hub import login

# Replace with your actual token
HF_TOKEN = "please get it from portal"  # Put your real token here
login(HF_TOKEN)
print("✅ Logged into Hugging Face")

# Now load the model
import torch
from transformers import pipeline

print("📥 Loading model (this will download ~5GB first time)...")

try:
    text_pipeline = pipeline(
        task="text-generation",
        model="google/gemma-3n-E4B-it",
        device=0,  # Use GPU
        torch_dtype=torch.bfloat16
    )
    print("✅ Model loaded successfully!")
    
    # Test simple generation
    print("\n🧪 Testing text generation...")
    response = text_pipeline(
        "The weather today is",
        max_new_tokens=20,
        do_sample=False
    )
    
    print(f"Input: 'The weather today is'")
    print(f"Output: '{response[0]['generated_text']}'")
    print("\n🎉 Gemma 3n is working!")
    
except Exception as e:
    print(f"❌ Error: {e}")