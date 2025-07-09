# Fine-tuning Emergency Classification Model - Gemma Kavach

## Overview

This section contains the fine-tuning pipeline for creating an emergency classification model as part of the Gemma Kavach crowd safety suite. The model is fine-tuned on Gemma 3n 2B to classify emergency situations in Indian contexts using Hinglish (Hindi-English mix) text.

## Model Details

- **Base Model**: `unsloth/gemma-3n-E2B-it`
- **Fine-tuning Method**: LoRA (Low-Rank Adaptation)
- **Dataset Size**: 60,000 samples (10,000 per class)
- **Classes**: 6 emergency categories
- **Language**: Hinglish (Hindi-English mix)

## Emergency Categories

1. **child_lost** - Lost children reports
2. **crowd_panic** - Crowd stampede/panic situations  
3. **lost_item** - Lost personal belongings
4. **medical_help** - Medical emergencies
5. **need_interpreter** - Translation/interpreter requests
6. **small_fire** - Small fire incidents

## Requirements

### Hardware
- **GPU**: RTX 4090 (24GB VRAM) or equivalent
- **Minimum VRAM**: 16GB for training
- **RAM**: 32GB+ recommended


### Environment Setup

Create a `.env` file with your API keys:
```
GEMINI_API_KEY=your_gemini_api_key_here
WANDB_API_KEY=your_wandb_api_key_here
```

## Quick Start

### Step 1: Generate Training Data

```bash
python data.py
```

This script will:
- Generate 10,000 samples per emergency class (60,000 total)
- Use Gemini API for synthetic data generation
- Save individual class files and combined dataset
- Support resume functionality for interrupted generation

**Generated Files:**
- `child_lost_10000.csv`
- `crowd_panic_10000.csv` 
- `lost_item_10000.csv`
- `medical_help_10000.csv`
- `need_interpreter_10000.csv`
- `small_fire_10000.csv`
- `emergency_dataset_60000.csv`

### Step 2: Fine-tune the Model

```bash
python job.py
```

**Training Configuration:**
- Batch size: 8
- Gradient accumulation: 2 steps
- Learning rate: 2e-5
- LoRA rank: 16
- Epochs: 2
- Optimizer: AdamW 8-bit
- Precision: bfloat16

### Step 3: Test the Model

```bash
python test.py
```

This will load your trained model and run interactive testing.

## Data Generation Details

### Synthetic Data Pipeline

The `data.py` script uses Gemini 2.5 Flash to generate realistic emergency scenarios:

```python
# Example prompt structure
prompt = """Generate 100 realistic examples of people reporting lost children 
in Hinglish (Hindi-English mix). Each example should be natural, urgent, 
and different from others."""
```

### Data Quality Features

- **Variety**: Each batch generates 100 unique samples
- **Resume Support**: Interrupted generation can be resumed
- **Progress Tracking**: Intermediate saves every 10 batches
- **Quality Control**: Realistic Indian emergency scenarios

### Sample Data Examples

```
child_lost: "Bacha kho gaya hai Zone D me"
medical_help: "Yahan ek aadmi behosh pada hai"
crowd_panic: "Log bhaag rahe hain, bheed me stampede ho raha"
small_fire: "Food stall me aag lagi hai"
```

## Fine-tuning Architecture

### Model Configuration

```python
model = FastModel.get_peft_model(
    model,
    r=16,                    # LoRA rank
    lora_alpha=16,           # LoRA alpha
    lora_dropout=0.1,        # Dropout rate
    bias="none",             # Bias configuration
    random_state=3407,       # Reproducibility
)
```

### Training Pipeline

1. **Data Preprocessing**: Convert to conversation format
2. **Tokenization**: Apply Gemma-3 chat template
3. **LoRA Training**: Parameter-efficient fine-tuning
4. **Response-only Training**: Focus on assistant responses
5. **Checkpointing**: Save every 250 steps

### Performance Monitoring

- **Weights & Biases**: Real-time training metrics
- **Memory Usage**: GPU memory tracking
- **Loss Tracking**: Training loss progression
- **Checkpoint Management**: Best model preservation

## Training Results

### Expected Performance

- **Training Time**: 2-4 hours on RTX 4090
- **Memory Usage**: ~18GB VRAM
- **Final Loss**: <0.1 (classification task)
- **Accuracy**: >95% on validation set

### Model Outputs

```
checkpoints/
├── emergency_2b_60k/
│   ├── checkpoint-250/
│   ├── checkpoint-500/
│   └── checkpoint-1750/
└── emergency_2b_60k_final/
    ├── adapter_model.safetensors
    ├── adapter_config.json
    └── training_stats.json
```

## Inference Usage

### Basic Classification

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load model
tokenizer = AutoTokenizer.from_pretrained("checkpoints/emergency_2b_60k_final")
model = AutoModelForCausalLM.from_pretrained("checkpoints/emergency_2b_60k_final")

# Classify emergency
text = "Bacha kho gaya hai"
prompt = f"Classify this emergency: {text}\nCategory:"
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=5)
prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
```

### Integration with Gemma Kavach

The fine-tuned model integrates with the main Gemma Kavach system:

```python
# In main application
def classify_emergency(text: str) -> str:
    response = requests.post("http://localhost:8000/classify", 
                           json={"text": text})
    return response.json()["category"]
```

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**
   - Reduce batch size to 4
   - Increase gradient accumulation steps
   - Use gradient checkpointing

2. **Generation Interrupted**
   - Run `data.py` again - it will resume automatically
   - Check `*_progress.csv` files for current status

3. **Model Loading Errors**
   - Ensure checkpoint path is correct
   - Check for corrupted checkpoint files
   - Try loading base model first

### Performance Optimization

```python
# For faster training
os.environ["UNSLOTH_COMPILE_DISABLE"] = "1"
os.environ["TORCH_USE_CUDA_DSA"] = "1"

# For memory efficiency
config.gradient_checkpointing = True
config.bf16 = True
config.tf32 = True
```

## File Structure

```
fine-tuning/
├── data.py              # Data generation script
├── job.py               # Fine-tuning script  
├── test.py              # Model testing script
├── .env                 # Environment variables
├── Datasets/            # Generated training data
│   ├── child_lost_10000.csv
│   ├── crowd_panic_10000.csv
│   └── ...
└── checkpoints/         # Model checkpoints
    └── emergency_2b_60k/
        ├── checkpoint-*/
        └── final/
```

## Advanced Configuration

### Custom Data Generation

Modify prompts in `data.py` for different scenarios:

```python
PROMPTS["new_category"] = {
    "model": NewCategorySample,
    "prompt": "Your custom prompt here..."
}
```

### Training Hyperparameters

Adjust in `job.py` for different setups:

```python
config = SFTConfig(
    per_device_train_batch_size=4,    # Reduce for less VRAM
    gradient_accumulation_steps=4,     # Increase for stability
    learning_rate=1e-5,               # Lower for fine-grained tuning
    warmup_steps=100,                 # Adjust warmup
    max_steps=5000,                   # Longer training
)
```

## Citation

If you use this fine-tuning pipeline in your research, please cite:

```bibtex
@software{gemma_kavach_finetuning,
  title={Gemma Kavach: Emergency Classification Fine-tuning Pipeline},
  author={Aditya Bhatt},
  year={2025},
  note={AI-powered crowd safety suite}
}
```

## License

This project is part of the Gemma Kavach suite. Please refer to the main project license for usage terms.

## Support

For issues related to fine-tuning:
1. Check the troubleshooting section above
2. Review Unsloth documentation
3. Monitor WandB training logs
4. Ensure proper environment setup

---

**Note**: This fine-tuning pipeline is optimized for Indian emergency scenarios and Hinglish text. For other languages or domains, modify the data generation prompts and training examples accordingly.