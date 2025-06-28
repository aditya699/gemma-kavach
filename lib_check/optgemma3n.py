# fast_gemma_inference.py
import torch
import time
from transformers import AutoModelForCausalLM, AutoTokenizer

print("🚀 Loading Gemma 3n for fast inference...")

# Use best precision for 4090
torch.set_float32_matmul_precision("high")

# Model & tokenizer
model_name = "google/gemma-3n-E4B-it"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="cuda",
    attn_implementation="eager"  # ✅ Required for Gemma
)

# Ensure tokenizer is complete
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Prepare input
prompt = "The weather is"
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

# Warm-up (JIT compilation, kernel load)
with torch.no_grad():
    _ = model.generate(**inputs, max_new_tokens=2)

# Inference test
start = time.time()
with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=15,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
        use_cache=True
    )
end = time.time()

# Decode and report
decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
speed = 15 / (end - start)

print(f"\n📝 Output: {decoded}")
print(f"⚡ Time: {end - start:.2f}s | Speed: {speed:.1f} tok/s")
