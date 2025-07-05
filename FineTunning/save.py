# -*- coding: utf-8 -*-
"""
Save the full trained model for inference
"""

# Fix for the typing compilation error
import builtins
from typing import Any
builtins.Any = Any

import torch
from unsloth import FastModel
from unsloth.chat_templates import get_chat_template

print("Loading your trained model to save it properly...")

# Load base model
model, tokenizer = FastModel.from_pretrained(
    model_name="unsloth/gemma-3n-E2B-it",
    max_seq_length=1024,
    load_in_4bit=True,
)

# Add LoRA adapters (same as training)
model = FastModel.get_peft_model(
    model,
    finetune_vision_layers=False,
    finetune_language_layers=True,
    finetune_attention_modules=True,
    finetune_mlp_modules=True,
    r=16,
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    random_state=3407,
)

# Set up chat template
tokenizer = get_chat_template(tokenizer, chat_template="gemma-3")

# Load your trained LoRA weights
print("Loading your trained weights...")
try:
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, "emergency_classifier_2b")
    print("✓ Loaded your trained LoRA adapters!")
except Exception as e:
    print(f"Error loading LoRA adapters: {e}")
    print("Trying alternative method...")
    try:
        # Alternative method using FastModel
        model.load_adapter("emergency_classifier_2b", adapter_name="default")
        print("✓ Loaded using alternative method!")
    except Exception as e2:
        print(f"Alternative method failed: {e2}")
        exit(1)

# Save as a complete merged model for inference
print("Saving as complete merged model...")
model.save_pretrained_merged("emergency_classifier_2b_merged", tokenizer, save_method="merged_16bit")

print("✓ Your trained model saved as 'emergency_classifier_2b_merged'")
print("Now you can use this for inference!")