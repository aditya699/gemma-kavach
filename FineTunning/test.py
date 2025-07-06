# test.py
import os
import torch
from unsloth import FastModel
from transformers import AutoTokenizer
from unsloth.chat_templates import get_chat_template

os.environ["UNSLOTH_COMPILE_DISABLE"] = "1"

# 1. Load base model
print("🔁 Loading base Gemma-3n E2B (4-bit)…")
model, _ = FastModel.from_pretrained(
    "unsloth/gemma-3n-E2B-it",
    load_in_4bit=True,
    dtype=torch.bfloat16,
    trust_remote_code=True,
)
print("✅ Base model loaded")

# 2. Load fine-tuned LoRA adapter
print("🧩 Loading LoRA adapter from checkpoints/emergency_classifier_2b_run1 …")
model.load_adapter("checkpoints/emergency_classifier_2b_run1", adapter_name="default")
print("✅ LoRA adapter loaded")

# 3. Load tokenizer with chat template
tokenizer = AutoTokenizer.from_pretrained("checkpoints/emergency_classifier_2b_run1")
tokenizer = get_chat_template(tokenizer, chat_template="gemma-3")

# 4. Few-shot classification function
def classify_emergency(text: str, max_tokens: int = 4) -> str:
    examples = [
        ("Bacha kho gaya hai", "child_lost"),
        ("Log dhakka-mukki kar rahe hain", "crowd_panic"),
        ("Mera bag kho gaya", "lost_item"),
        ("Mujhe doctor chahiye", "medical_help"),
        ("Mujhe interpreter chahiye", "need_interpreter"),
        ("Yahan aag lag gayi hai", "small_fire"),
    ]

    few_shot = "\n".join([f"Emergency: {ex}\nCategory: {label}" for ex, label in examples])
    prompt = f"{few_shot}\nEmergency: {text}\nCategory:"

    conversation = [
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": ""},
    ]

    batch = tokenizer.apply_chat_template(
        conversation,
        tokenize=True,
        return_tensors="pt",
        return_dict=True,
        add_generation_prompt=True,
    ).to("cuda")

    with torch.inference_mode():
        out = model.generate(
            **batch,
            max_new_tokens=max_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    gen_tokens = out[0][batch["input_ids"].shape[-1]:]
    reply = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()
    return reply.lower().split()[0]

# 5. Run a test batch
if __name__ == "__main__":
    print("🧪 Running classification tests...\n")

    examples = [
        "Bacha kho gaya hai",
        "Mujhe turant doctor chahiye",
        "Zone D me log bhaag rahe hain",
        "Yahan se dhuaan nikal raha hai",
        "Tourist ko interpreter chahiye",
        "Mere saman ka pata nahi chal raha",
        "Log bahut tez dhakka de rahe hain",
        "Kisi ka beta kho gaya hai",
        "Yahan fire extinguisher chahiye",
        "Doctor ka booth kaha hai?",
    ]

    for ex in examples:
        result = classify_emergency(ex)
        print(f"{ex:<50} → {result}")
