# # test_speed.py
# print("🚀 Testing speed on already-loaded model...")

# import torch
# from transformers import pipeline
# from huggingface_hub import login
# import time

# # Login (quick since already cached)
# HF_TOKEN = "please get it from portal"  # Replace with yours
# login(HF_TOKEN)

# # Load model (should be faster now - using cached files)
# print("📥 Loading model from cache...")
# start_time = time.time()

# text_pipeline = pipeline(
#     task="text-generation",
#     model="google/gemma-3n-E4B-it",
#     device=0,
#     torch_dtype=torch.bfloat16
# )

# load_time = time.time() - start_time
# print(f"✅ Model loaded in {load_time:.2f} seconds")

# # Test generation speed
# print("\n🧪 Testing generation speed...")
# start_time = time.time()

# response = text_pipeline(
#     "Explain AI in simple terms:",
#     max_new_tokens=50,
#     do_sample=False
# )

# gen_time = time.time() - start_time
# print(f"⚡ Generation completed in {gen_time:.2f} seconds")
# print(f"📝 Output: '{response[0]['generated_text']}'")
# test_optimized.py
print("🚀 Testing with optimizations...")

import torch
from transformers import pipeline
from huggingface_hub import login
import time

# Optimize PyTorch settings
torch.set_float32_matmul_precision('high')  # Use TensorFloat32
torch._dynamo.config.suppress_errors = True  # Avoid compilation issues

# Login
HF_TOKEN = "please get it from portal" 
login(HF_TOKEN)

print("📥 Loading optimized model...")
start_time = time.time()

text_pipeline = pipeline(
    task="text-generation",
    model="google/gemma-3n-E4B-it",
    device=0,
    torch_dtype=torch.bfloat16
)

load_time = time.time() - start_time
print(f"✅ Model loaded in {load_time:.2f} seconds")

# Test shorter generation first
print("\n🧪 Testing short generation...")
start_time = time.time()

response = text_pipeline(
    "AI is",
    max_new_tokens=10,  # Shorter first
    do_sample=False,
    pad_token_id=text_pipeline.tokenizer.eos_token_id
)

gen_time = time.time() - start_time
print(f"⚡ Short generation: {gen_time:.2f} seconds")
print(f"📝 Output: '{response[0]['generated_text']}'")

# Test normal generation
print("\n🧪 Testing normal generation...")
start_time = time.time()

response = text_pipeline(
    "The future of AI:",
    max_new_tokens=30,
    do_sample=False,
    pad_token_id=text_pipeline.tokenizer.eos_token_id
)

gen_time = time.time() - start_time
print(f"⚡ Normal generation: {gen_time:.2f} seconds")
print(f"📝 Output: '{response[0]['generated_text']}'")