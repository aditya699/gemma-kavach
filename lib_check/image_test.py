# test_their_method.py
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
from PIL import Image
import requests
import tempfile
import time

torch._dynamo.config.suppress_errors = True

processor = AutoProcessor.from_pretrained("google/gemma-3n-E4B-it")
model = AutoModelForImageTextToText.from_pretrained(
    "google/gemma-3n-E4B-it", torch_dtype=torch.bfloat16
).to("cuda")

# Download image and save as temp file (their approach)
image_url = "https://ai.google.dev/static/gemma/docs/images/thali-indian-plate.jpg"
response = requests.get(image_url)
with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
    img_path = tmp.name
    tmp.write(response.content)

# Their message format
messages = [
    {
        "role": "system",
        "content": [{"type": "text", "text": "You are a friendly assistant."}],
    },
    {
        "role": "user",
        "content": [
            {"type": "image", "image": img_path},
            {"type": "text", "text": "What's in this image give consise reults?"},
        ],
    },
]

print("🧪 Testing their approach...")
start = time.time()

# Their processing method
inputs = processor.apply_chat_template(
    messages,
    add_generation_prompt=True,
    tokenize=True,
    return_dict=True,
    return_tensors="pt",
).to(model.device, dtype=model.dtype)

with torch.inference_mode():
    outputs = model.generate(**inputs, max_new_tokens=100, disable_compile=True)

# Their decoding method
reply = processor.decode(
    outputs[0][inputs["input_ids"].shape[-1]:], 
    skip_special_tokens=True
)

total_time = time.time() - start
print(f"⚡ Time: {total_time:.2f}s")
print(f"📝 Response: {reply}")

# Cleanup
import os
os.remove(img_path)