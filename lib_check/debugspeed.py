# import torch
# import time
# from transformers import AutoModelForCausalLM, AutoTokenizer
# from huggingface_hub import login
# import os

# print("🔧 Fixing compilation issues...")

# # Disable PyTorch graph optimizations
# torch._dynamo.config.suppress_errors = True
# torch._dynamo.config.disable = True
# torch.backends.cudnn.benchmark = False
# torch.set_float32_matmul_precision('high')

# # Disable compile-related env
# os.environ['TORCH_COMPILE'] = '0'
# os.environ['PYTORCH_DISABLE_DYNAMO'] = '1'

# # Login to Hugging Face
# login(token="please get it from portal")  # Replace with your actual token

# print("🚀 Loading model with compilation disabled...")

# model = AutoModelForCausalLM.from_pretrained(
#     "google/gemma-3n-E4B-it",
#     torch_dtype=torch.bfloat16,
#     attn_implementation="eager"
# ).to("cuda")

# tokenizer = AutoTokenizer.from_pretrained("google/gemma-3n-E4B-it")
# if tokenizer.pad_token is None:
#     tokenizer.pad_token = tokenizer.eos_token

# print("✅ Model loaded with optimizations disabled")

# # Test
# for i in range(1):
#     print(f"\n🧪 Test run {i+1}...")
#     input_text = "How is India using AI?"
#     inputs = tokenizer(input_text, return_tensors="pt").to("cuda")
    
#     start_time = time.time()
#     with torch.no_grad():
#         outputs = model.generate(
#             **inputs,
#             max_new_tokens=100,
#             do_sample=False,
#             pad_token_id=tokenizer.eos_token_id,
#             use_cache=True
#         )
#     inference_time = time.time() - start_time
    
#     result = tokenizer.decode(outputs[0], skip_special_tokens=True)
#     tokens_per_sec = 600 / inference_time
    
#     print(f"⚡ Time: {inference_time:.2f}s | Speed: {tokens_per_sec:.1f} tok/s")
#     print(f"📝 Result: '{result}'")

# transformers_streaming.py
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextStreamer
from huggingface_hub import login
import time

torch._dynamo.config.suppress_errors = True
login(token="please get it from portal")

print("🌊 Transformers with Streaming...")

model = AutoModelForCausalLM.from_pretrained(
    "google/gemma-3n-E4B-it",
    torch_dtype=torch.bfloat16,
    attn_implementation="eager"
).to("cuda")

tokenizer = AutoTokenizer.from_pretrained("google/gemma-3n-E4B-it")
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Create a streaming tokenizer
streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

input_text = "How is India using AI in agriculture?"
inputs = tokenizer(input_text, return_tensors="pt").to("cuda")

print("📝 Response: ", end="")
start_time = time.time()

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=100,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
        streamer=streamer  # This enables streaming!
    )

total_time = time.time() - start_time
print(f"\n⚡ Total time: {total_time:.2f}s")