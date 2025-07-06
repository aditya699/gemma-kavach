# -*- coding: utf-8 -*-
"""
Fine-tune Gemma 3N 2B for Emergency Classification - BIG RUN (60K samples)
Fixed version based on working original script
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
import time
from datetime import datetime

# Optional wandb setup
try:
    import wandb
    WANDB_AVAILABLE = True
    print("✅ Wandb available - will track metrics")
except ImportError:
    WANDB_AVAILABLE = False
    print("📝 Wandb not available - using local logging only")

print("🚀 STARTING BIG RUN - Emergency Classification 2B Model")
print("=" * 60)
print("Target: 60K samples | Expected training time: 3-4 hours")
print("The Bitter Lesson: Scale is all you need!")
print("=" * 60)

print("Loading Gemma 3N 2B model...")

from unsloth import FastModel

model, tokenizer = FastModel.from_pretrained(
    model_name="unsloth/gemma-3n-E2B-it",
    dtype=None,
    max_seq_length=1024,  # Keep same as original working script
    load_in_4bit=True,
)

print("✅ Model loaded successfully!")

print("Adding LoRA adapters...")
model = FastModel.get_peft_model(
    model,
    finetune_vision_layers=False,
    finetune_language_layers=True,
    finetune_attention_modules=True,
    finetune_mlp_modules=True,
    r=32,  # Increased for big run
    lora_alpha=32,
    lora_dropout=0.05,  # Small dropout for large dataset
    bias="none",
    random_state=3407,
)

from unsloth.chat_templates import get_chat_template
tokenizer = get_chat_template(tokenizer, chat_template="gemma-3")

print("Loading datasets...")

# Updated to use 10K sample files in Datasets folder
csv_files = [
    "Datasets/child_lost_10000.csv",
    "Datasets/crowd_panic_10000.csv", 
    "Datasets/lost_item_10000.csv",
    "Datasets/medical_help_10000.csv",
    "Datasets/need_interpreter_10000.csv",
    "Datasets/small_fire_10000.csv"
]

datasets = []
total_loaded = 0

for file in csv_files:
    try:
        df = pd.read_csv(file)
        datasets.append(df)
        total_loaded += len(df)
        print(f"✅ Loaded {file}: {len(df):,} samples")
    except FileNotFoundError:
        print(f"❌ Warning: {file} not found, skipping...")

if datasets:
    combined_df = pd.concat(datasets, ignore_index=True)
    print(f"\n📊 DATASET STATISTICS:")
    print(f"Total samples loaded: {len(combined_df):,}")
    
    # Show class distribution
    class_counts = combined_df['label'].value_counts()
    print(f"Class distribution:")
    for class_name, count in class_counts.items():
        print(f"  {class_name:20}: {count:,}")
    
    # Shuffle the dataset
    combined_df = combined_df.sample(frac=1, random_state=3407).reset_index(drop=True)
    print(f"✅ Dataset shuffled")

    # Create conversations - EXACTLY like the original working script
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
    print(f"✅ Created dataset with {len(dataset):,} conversations")

    # Format prompts - EXACTLY like the original working script
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

    print("\n⚙️ SETTING UP BIG RUN TRAINING CONFIG...")
    
    # Calculate steps based on data size
    total_train_samples = len(dataset)
    batch_size = 16  # 4 * 4 gradient accumulation
    steps_per_epoch = total_train_samples // batch_size
    epochs = 3
    max_steps = steps_per_epoch * epochs
    
    print(f"📊 TRAINING CALCULATIONS:")
    print(f"Total training samples: {total_train_samples:,}")
    print(f"Effective batch size: {batch_size}")
    print(f"Steps per epoch: {steps_per_epoch:,}")
    print(f"Target epochs: {epochs}")
    print(f"Total training steps: {max_steps:,}")

    # Setup logging
    log_file = f"training_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    def log_message(message):
        """Log message to both console and file"""
        print(message)
        with open(log_file, "a") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

    # Initialize wandb if available
    if WANDB_AVAILABLE:
        try:
            wandb.init(
                project="emergency-classification-2b",
                name=f"big-run-{datetime.now().strftime('%Y%m%d-%H%M')}",
                config={
                    "model": "gemma-3n-2b",
                    "dataset_size": total_train_samples,
                    "batch_size": batch_size,
                    "learning_rate": 3e-5,
                    "max_steps": max_steps,
                    "lora_rank": 32,
                }
            )
            report_to = "wandb"
            log_message("✅ Wandb initialized successfully")
        except Exception as e:
            log_message(f"⚠️ Wandb init failed: {e}, using local logging only")
            report_to = "none"
            WANDB_AVAILABLE = False
    else:
        report_to = "none"
        log_message("📝 Using local logging only")

    print("Setting up trainer config...")
    config = SFTConfig(
        dataset_text_field="text",
        per_device_train_batch_size=4,  # Increased from original 2
        gradient_accumulation_steps=4,  # Reduced from original 8
        warmup_steps=100,  # Increased from original 50
        max_steps=max_steps,  # Calculated based on dataset size
        learning_rate=3e-5,  # Reduced from original 5e-5 for stability
        logging_steps=50,  # Increased from original 10
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=3407,
        report_to=report_to,
        output_dir="checkpoints/emergency_classifier_2b_big_run",
        save_steps=500,  # More frequent saves for big run
        save_total_limit=3,  # Keep more checkpoints
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

    print("✅ Trainer configured for response-only fine-tuning")

    if torch.cuda.is_available():
        gpu_stats = torch.cuda.get_device_properties(0)
        start_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
        max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)
        print(f"\n🖥️ GPU INFO:")
        print(f"GPU: {gpu_stats.name}")
        print(f"Memory: {start_memory:.1f}/{max_memory:.1f} GB")

    print(f"\n🚀 STARTING BIG RUN TRAINING...")
    print(f"Estimated time: {max_steps * 0.8 / 3600:.1f} hours")
    print("=" * 60)

    try:
        # Start training (don't resume from checkpoint on first run)
        log_message("🔄 Starting training...")
        trainer_stats = trainer.train()
        
        log_message(f"✅ Training completed in {trainer_stats.metrics['train_runtime']:.2f} seconds")
        log_message(f"📊 Final training loss: {trainer_stats.metrics.get('train_loss', 'N/A')}")

        print("💾 Saving model...")
        model.save_pretrained("checkpoints/emergency_classifier_2b_big_run_final")
        tokenizer.save_pretrained("checkpoints/emergency_classifier_2b_big_run_final")
        print("✅ Model saved successfully!")

        # Save training stats
        with open("checkpoints/emergency_classifier_2b_big_run_final/training_stats.json", "w") as f:
            json.dump(trainer_stats.metrics, f, indent=2)
        log_message("📊 Training statistics saved!")

    except Exception as e:
        log_message(f"❌ Training error: {e}")
        print("💾 Saving partial model...")
        try:
            model.save_pretrained("checkpoints/emergency_classifier_2b_big_run_partial")
            tokenizer.save_pretrained("checkpoints/emergency_classifier_2b_big_run_partial")
            print("✅ Partial model saved.")
        except Exception as save_error:
            print(f"❌ Save failed: {save_error}")

    # Close wandb if it was used
    if WANDB_AVAILABLE:
        try:
            wandb.finish()
            log_message("✅ Wandb session closed")
        except:
            pass

else:
    print("❌ No datasets found! Please check your CSV paths.")
    print("Expected files:")
    for file in csv_files:
        print(f"  - {file}")

print("\n🎉 BIG RUN COMPLETED!")
print("The Bitter Lesson strikes again: More data + more compute = magic! ✨")