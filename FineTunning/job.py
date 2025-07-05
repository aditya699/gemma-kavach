# -*- coding: utf-8 -*-
"""
Fine-tune Gemma 3N 2B for Emergency Classification (Big Run)
"""
import os
os.environ["UNSLOTH_COMPILE_DISABLE"] = "1"
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
os.environ["TORCH_USE_CUDA_DSA"] = "1"

import builtins
from typing import Any
builtins.Any = Any

import torch
import pandas as pd
from datasets import Dataset

print("Loading Gemma 3N 2B model...")

from unsloth import FastModel

model, tokenizer = FastModel.from_pretrained(
    model_name="unsloth/gemma-3n-E2B-it",
    dtype=None,
    max_seq_length=1024,
    load_in_4bit=True,
)

print("Model loaded successfully!")

print("Adding LoRA adapters...")
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

from unsloth.chat_templates import get_chat_template
tokenizer = get_chat_template(tokenizer, chat_template="gemma-3")

print("Loading datasets...")

csv_files = [
    "Datasets/child_lost_100.csv",
    "Datasets/crowd_panic_100.csv", 
    "Datasets/lost_item_100.csv",
    "Datasets/medical_help_100.csv",
    "Datasets/need_interpreter_100.csv",
    "Datasets/small_fire_100.csv"
]

datasets = []
for file in csv_files:
    try:
        df = pd.read_csv(file)
        datasets.append(df)
        print(f"Loaded {file}: {len(df)} samples")
    except FileNotFoundError:
        print(f"Warning: {file} not found, skipping...")

if datasets:
    combined_df = pd.concat(datasets, ignore_index=True)
    print(f"Total samples: {len(combined_df)}")

    conversations = []
    for _, row in combined_df.iterrows():
        conversation = [
            {
                "role": "user",
                "content": f"Classify this emergency: {row['text']}"
            },
            {
                "role": "assistant", 
                "content": f"Category: {row['label']}"
            }
        ]
        conversations.append({"conversations": conversation})

    dataset = Dataset.from_list(conversations)
    print(f"Created dataset with {len(dataset)} conversations")

    def formatting_prompts_func(examples):
        convos = examples["conversations"]
        texts = [tokenizer.apply_chat_template(
            convo, tokenize=False, add_generation_prompt=False
        ).removeprefix('<bos>') for convo in convos]
        return {"text": texts}

    dataset = dataset.map(formatting_prompts_func, batched=True)

    print("Sample formatted conversation:")
    print(dataset[0]["text"][:200] + "...")

    from trl import SFTTrainer, SFTConfig

    print("Setting up trainer...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=SFTConfig(
            dataset_text_field="text",
            per_device_train_batch_size=2,           # Can increase if VRAM allows
            gradient_accumulation_steps=8,            # Larger batch via accumulation
            warmup_steps=50,
            max_steps=1000,                           # 🔥 Bigger run
            learning_rate=5e-5,                       # More aggressive learning
            logging_steps=10,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="cosine",
            seed=3407,
            report_to="none",
        ),
    )

    from unsloth.chat_templates import train_on_responses_only
    trainer = train_on_responses_only(
        trainer,
        instruction_part="<start_of_turn>user\n",
        response_part="<start_of_turn>model\n",
    )

    print("Trainer configured for response-only fine-tuning")

    if torch.cuda.is_available():
        gpu_stats = torch.cuda.get_device_properties(0)
        start_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
        max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)
        print(f"GPU: {gpu_stats.name} | Memory: {start_memory}/{max_memory} GB")

    print("Starting training...")
    try:
        trainer_stats = trainer.train()
        print(f"Training completed in {trainer_stats.metrics['train_runtime']:.2f} seconds")

        print("Saving model...")
        model.save_pretrained("checkpoints/emergency_classifier_2b_run1")
        tokenizer.save_pretrained("checkpoints/emergency_classifier_2b_run1")
        print("Model saved successfully!")

    except Exception as e:
        print(f"Training error: {e}")
        print("Saving partial model...")
        try:
            model.save_pretrained("checkpoints/emergency_classifier_2b_partial")
            tokenizer.save_pretrained("checkpoints/emergency_classifier_2b_partial")
            print("Partial model saved.")
        except Exception as save_error:
            print(f"Save failed: {save_error}")

else:
    print("❌ No datasets found! Please check your CSV paths.")

print("✅ Script completed.")
