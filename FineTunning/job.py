# -*- coding: utf-8 -*-
"""
Emergency Classification - Gemma 3N 2B Fine-tuning (60K samples)
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
import json
from datetime import datetime
import wandb

print("🚀 Emergency Classification Training - 60K Samples")
print("=" * 50)

wandb.init(
    project="emergency-classification-2b",
    name=f"60k-fast-{datetime.now().strftime('%Y%m%d-%H%M')}",
    config={
        "model": "gemma-3n-2b",
        "batch_size": 8,
        "learning_rate": 2e-5,
        "lora_rank": 16,
        "epochs": 2,
        "optimization": "fast_batch_size",
    }
)

from unsloth import FastModel

model, tokenizer = FastModel.from_pretrained(
    model_name="unsloth/gemma-3n-E2B-it",
    dtype=None,
    max_seq_length=1024,
    load_in_4bit=True,
)

model = FastModel.get_peft_model(
    model,
    finetune_vision_layers=False,
    finetune_language_layers=True,
    finetune_attention_modules=True,
    finetune_mlp_modules=True,
    r=16,
    lora_alpha=16,
    lora_dropout=0.1,
    bias="none",
    random_state=3407,
)

from unsloth.chat_templates import get_chat_template
tokenizer = get_chat_template(tokenizer, chat_template="gemma-3")

csv_files = [
    "Datasets/child_lost_10000.csv",
    "Datasets/crowd_panic_10000.csv", 
    "Datasets/lost_item_10000.csv",
    "Datasets/medical_help_10000.csv",
    "Datasets/need_interpreter_10000.csv",
    "Datasets/small_fire_10000.csv"
]

datasets = []
for file in csv_files:
    try:
        df = pd.read_csv(file)
        datasets.append(df)
        print(f"✅ {file}: {len(df):,} samples")
    except FileNotFoundError:
        print(f"❌ {file} not found")

combined_df = pd.concat(datasets, ignore_index=True)
print(f"📊 Total samples: {len(combined_df):,}")

class_counts = combined_df['label'].value_counts()
for class_name, count in class_counts.items():
    print(f"  {class_name}: {count:,}")

combined_df = combined_df.sample(frac=1, random_state=3407).reset_index(drop=True)

categories = sorted(combined_df['label'].unique().tolist())
categories_str = ", ".join(categories)
print(f"Categories: {categories_str}")

conversations = []
for _, row in combined_df.iterrows():
    conversation = [
        {"role": "user", "content": f"Classify this emergency into one of these categories: {categories_str}\n\nEmergency: {row['text']}"},
        {"role": "assistant", "content": f"{row['label']}"}
    ]
    conversations.append({"conversations": conversation})

dataset = Dataset.from_list(conversations)
print(f"✅ Dataset created: {len(dataset):,} conversations")

def formatting_prompts_func(examples):
    convos = examples["conversations"]
    texts = [tokenizer.apply_chat_template(
        convo, tokenize=False, add_generation_prompt=False
    ).removeprefix('<bos>') for convo in convos]
    return {"text": texts}

dataset = dataset.map(formatting_prompts_func, batched=True)

from trl import SFTTrainer, SFTConfig

total_samples = len(dataset)
batch_size = 8
grad_accum = 2
effective_batch_size = batch_size * grad_accum
steps_per_epoch = total_samples // effective_batch_size
epochs = 2
max_steps = steps_per_epoch * epochs

print(f"\n⚙️ Training Config:")
print(f"Total samples: {total_samples:,}")
print(f"Effective batch size: {effective_batch_size}")
print(f"Max steps: {max_steps:,}")
print(f"Estimated time: {max_steps * 1.2 / 3600:.1f} hours")

config = SFTConfig(
    dataset_text_field="text",
    per_device_train_batch_size=8,  # Increased from 2 to 8
    gradient_accumulation_steps=2,  # Reduced from 8 to 2
    warmup_steps=200,
    max_steps=max_steps,
    learning_rate=2e-5,
    logging_steps=25,
    optim="adamw_8bit",
    weight_decay=0.01,
    lr_scheduler_type="cosine",
    seed=3407,
    report_to="wandb",
    output_dir="checkpoints/emergency_2b_60k",
    save_steps=250,
    save_total_limit=3,
    bf16=True,
    tf32=True,  # Faster on RTX 4090
    gradient_checkpointing=True,
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    args=config,
)

from unsloth.chat_templates import train_on_responses_only
trainer = train_on_responses_only(
    trainer,
    instruction_part="<start_of_turn>user\n",
    response_part="<start_of_turn>model\n",
)

if torch.cuda.is_available():
    gpu_stats = torch.cuda.get_device_properties(0)
    start_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
    max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)
    print(f"\n🖥️ GPU: {gpu_stats.name}")
    print(f"Memory: {start_memory:.1f}/{max_memory:.1f} GB")

print(f"\n🚀 Starting Training...")
print("Monitor at: https://wandb.ai")
print("=" * 50)

try:
    trainer_stats = trainer.train()
    
    print(f"✅ Training completed!")
    print(f"Final loss: {trainer_stats.metrics.get('train_loss', 'N/A')}")
    
    model.save_pretrained("checkpoints/emergency_2b_60k_final")
    tokenizer.save_pretrained("checkpoints/emergency_2b_60k_final")
    
    with open("checkpoints/emergency_2b_60k_final/training_stats.json", "w") as f:
        json.dump(trainer_stats.metrics, f, indent=2)
    
    print("✅ Model saved!")

except Exception as e:
    print(f"❌ Training error: {e}")
    model.save_pretrained("checkpoints/emergency_2b_60k_partial")
    tokenizer.save_pretrained("checkpoints/emergency_2b_60k_partial")
    print("✅ Partial model saved")

wandb.finish()
print("🎉 Training completed!")