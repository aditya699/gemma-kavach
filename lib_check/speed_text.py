# fixed_text_comparison.py
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import login
import time

torch._dynamo.config.suppress_errors = True
login(token="please get it from portal")

model = AutoModelForCausalLM.from_pretrained(
    "google/gemma-3n-E4B-it",
    torch_dtype=torch.bfloat16,
    attn_implementation="eager"
).to("cuda")

tokenizer = AutoTokenizer.from_pretrained("google/gemma-3n-E4B-it")
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

prompt = "Explain how AI is transforming agriculture in India"

print("🔄 Comparing Text Generation Methods...")

# ------- OUR CURRENT METHOD -------
print("\n1️⃣ OUR METHOD:")
start = time.time()

inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=100,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
        use_cache=True
    )

result1 = tokenizer.decode(outputs[0], skip_special_tokens=True)
time1 = time.time() - start

print(f"⚡ Time: {time1:.2f}s")
print(f"📝 Response: {result1[:200]}...")

# ------- THEIR METHOD (FIXED) -------
print("\n2️⃣ THEIR METHOD (FIXED):")
start = time.time()

# Their message format with system context
messages = [
    {
        "role": "system", 
        "content": "You are a knowledgeable AI assistant."
    },
    {
        "role": "user",
        "content": prompt
    },
]

# Fixed processing method
chat_template = tokenizer.apply_chat_template(
    messages,
    add_generation_prompt=True,
    tokenize=False,  # Get text first
    return_tensors=None
)

# Then tokenize separately
inputs = tokenizer(chat_template, return_tensors="pt").to("cuda")

with torch.inference_mode():  # Their inference mode
    outputs = model.generate(
        **inputs, 
        max_new_tokens=100, 
        disable_compile=True,  # Their stability flag
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id
    )

# Their decoding method (extract only new tokens)
result2 = tokenizer.decode(
    outputs[0][inputs["input_ids"].shape[-1]:], 
    skip_special_tokens=True
)

time2 = time.time() - start

print(f"⚡ Time: {time2:.2f}s")
print(f"📝 Response: {result2[:200]}...")

# ------- COMPARISON -------
print(f"\n📊 COMPARISON:")
print(f"Our method:    {time1:.2f}s")
print(f"Their method:  {time2:.2f}s")
print(f"Speed diff:    {((time1-time2)/time1)*100:.1f}% {'faster' if time2 < time1 else 'slower'}")

print(f"\n📝 FULL RESPONSES:")
print(f"\n🔹 Our method full response:\n{result1}")
print(f"\n🔹 Their method full response:\n{result2}")