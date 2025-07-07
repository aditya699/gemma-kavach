# test.py - Simple approach using transformers directly
import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import BitsAndBytesConfig

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

print("🔁 Loading your trained model...")

# Try to load directly from latest checkpoint
try:
    # Load from the latest checkpoint (step 1750)
    checkpoint_path = "checkpoints/emergency_2b_60k/checkpoint-1750"
    tokenizer = AutoTokenizer.from_pretrained(checkpoint_path)
    
    # 4-bit quantization config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
    )
    
    # Load model from checkpoint
    model = AutoModelForCausalLM.from_pretrained(
        checkpoint_path,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True
    )
    
    print("✅ Model loaded from checkpoint-1750")
    
except Exception as e:
    print(f"❌ Checkpoint loading failed: {e}")
    print("🔄 Trying alternative loading method...")
    
    # Alternative: Try unsloth loading
    try:
        from unsloth import FastModel
        model, tokenizer = FastModel.from_pretrained(
            "unsloth/gemma-3n-E2B-it",
            load_in_4bit=True,
            dtype=torch.bfloat16,
        )
        
        # Try to load the checkpoint as LoRA
        model.load_adapter("checkpoints/emergency_2b_60k/checkpoint-1750", adapter_name="emergency")
        print("✅ LoRA adapter loaded from checkpoint-1750")
        
    except Exception as e2:
        print(f"❌ Alternative loading failed: {e2}")
        print("🔄 Using base model...")
        
        # Final fallback: base model only
        tokenizer = AutoTokenizer.from_pretrained("unsloth/gemma-3n-E2B-it")
        
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )
        
        model = AutoModelForCausalLM.from_pretrained(
            "unsloth/gemma-3n-E2B-it",
            quantization_config=bnb_config,
            device_map="auto",
            torch_dtype=torch.bfloat16,
            trust_remote_code=True
        )

# Ensure tokenizer has pad token
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print("🧪 Model ready for testing!")

# Categories from your training
categories = ["child_lost", "crowd_panic", "lost_item", "medical_help", "need_interpreter", "small_fire"]
categories_str = ", ".join(categories)

def classify_emergency(text: str) -> str:
    """Classify emergency text"""
    
    # Create prompt exactly like training
    prompt = f"Classify this emergency into one of these categories: {categories_str}\n\nEmergency: {text}\n\nCategory:"
    
    # Tokenize
    inputs = tokenizer(
        prompt, 
        return_tensors="pt", 
        padding=True, 
        truncation=True,
        max_length=512
    ).to(model.device)
    
    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=5,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
            temperature=0.1,
        )
    
    # Decode response
    generated_tokens = outputs[0][inputs["input_ids"].shape[-1]:]
    response = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
    
    # Extract category
    response_lower = response.lower()
    for category in categories:
        if category in response_lower:
            return category
    
    return response_lower.split()[0] if response_lower else "unknown"

# Test the model
if __name__ == "__main__":
    print(f"\n📋 Categories: {categories_str}")
    print("\n🧪 Running tests...\n")
    
    test_cases = [
        "Bacha kho gaya hai",
        "Mujhe doctor chahiye", 
        "Log bhag rahe hain",
        "Yahan aag lagi hai",
        "I need interpreter",
        "Mera bag kho gaya"
    ]
    
    print(f"{'Emergency':<30} → {'Prediction'}")
    print("=" * 50)
    
    for test in test_cases:
        try:
            prediction = classify_emergency(test)
            print(f"{test:<30} → {prediction}")
        except Exception as e:
            print(f"{test:<30} → ERROR: {e}")
    
    print("\n🎯 Interactive testing:")
    while True:
        user_input = input("\nEnter emergency (or 'quit'): ")
        if user_input.lower() == 'quit':
            break
        
        try:
            result = classify_emergency(user_input)
            print(f"→ {result}")
        except Exception as e:
            print(f"→ ERROR: {e}")
    
    print("✅ Testing completed!")