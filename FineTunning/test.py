# run_emergency.py
# -----------------------------------------------------------
# Inference helper for the Gemma-3n emergency-classifier LoRA
# -----------------------------------------------------------
import os
import torch
from unsloth import FastModel
from transformers import AutoTokenizer
from unsloth.chat_templates import get_chat_template

# (optional) keep Unsloth from compiling Triton kernels
os.environ["UNSLOTH_COMPILE_DISABLE"] = "1"

# 1️⃣  Load the *base* Gemma-3n model in 4-bit
print("Loading base Gemma-3n E2B (4-bit)…")
model, _ = FastModel.from_pretrained(
    "unsloth/gemma-3n-E2B-it",
    load_in_4bit=True,           # same as training
    dtype=torch.bfloat16,        # or None / fp16
    trust_remote_code=True,
)
print("✔️  Base model ready")

# 2️⃣  Attach your fine-tuned LoRA adapter
print("Loading LoRA adapter: emergency_classifier_2b …")
model.load_adapter("emergency_classifier_2b")   # folder with adapter_model.bin
model.eval()                                    # DON’T .to("cuda") for 4-bit
print("✔️  Adapter loaded")

# 3️⃣  Load the tokenizer saved after training (carries Gemma-3 template)
tokenizer = AutoTokenizer.from_pretrained("emergency_classifier_2b")
tokenizer = get_chat_template(tokenizer, chat_template="gemma-3")

# 4️⃣  Single-call classifier
def classify_emergency(text: str, max_tokens: int = 8) -> str:
    # Build conversation EXACTLY like training
    conversation = [
        {"role": "user",
         "content": f"Classify this emergency: {text}"},
        {"role": "assistant", "content": ""},          # generation slot
    ]

    batch = tokenizer.apply_chat_template(
        conversation,
        tokenize=True,
        return_tensors="pt",
        return_dict=True,          # -> BatchEncoding (mapping of tensors)
        add_generation_prompt=True,
    ).to("cuda")                   # one call moves every tensor to GPU

    with torch.inference_mode():
        out = model.generate(
            **batch,
            max_new_tokens=max_tokens,
            do_sample=False,       # greedy for deterministic label
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    gen_tokens = out[0][batch["input_ids"].shape[-1]:]   # new tokens only
    reply = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()
    return reply.replace("Category:", "").strip()

# 5️⃣  Quick sanity check
if __name__ == "__main__":
    examples = [
        "Bacha kho gaya hai",
        "Yahan aag lag gayi",
        "Mujhe doctor chahiye",
        "Log dhakka-mukki kar rahe hain",
    ]
    for ex in examples:
        print(f"{ex:<35} → {classify_emergency(ex)}")
