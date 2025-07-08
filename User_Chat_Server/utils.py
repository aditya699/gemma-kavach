# utils.py - Complete file with model loading + emergency functions
import os

# AGGRESSIVE compilation disable BEFORE any imports
os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
os.environ["TORCH_USE_CUDA_DSA"] = "1"

import torch

# Disable all torch compilation
torch._dynamo.config.disable = True
torch._dynamo.config.suppress_errors = True
torch.backends.cudnn.benchmark = False
torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32 = False

import unsloth  # Import unsloth first to avoid warnings
from transformers import AutoTokenizer, BitsAndBytesConfig, AutoModelForCausalLM
import logging

# Emergency report imports
import smtplib
import uuid
import time
from email.message import EmailMessage
from google.cloud import storage
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("transformers").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Global variables for model and tokenizer
model = None
tokenizer = None

# Categories
CATEGORIES = ["child_lost", "crowd_panic", "lost_item", "medical_help", "need_interpreter", "small_fire"]
CATEGORIES_STR = ", ".join(CATEGORIES)

# Email Configuration
EMAIL_SENDER = "ab0358031@gmail.com"
EMAIL_PASSWORD = os.getenv("GOOGLE_APP_PASSWORD")
EMAIL_RECEIVER = "ab0358031@gmail.com"

# GCS Configuration
EMERGENCY_BUCKET = os.getenv("BUCKET_NAME", "your-bucket-name")
EMERGENCY_IMAGES_PREFIX = "emergency_reports/"

def load_model():
    """Load fine-tuned model with LoRA - NO FALLBACKS!"""
    global model, tokenizer
    
    try:
        logger.info("Loading base model + LoRA adapter (GPU only)...")
        
        from unsloth import FastModel
        
        # Load base model directly on GPU
        model, tokenizer = FastModel.from_pretrained(
            "unsloth/gemma-3n-E2B-it",
            load_in_4bit=True,
            dtype=torch.bfloat16,
        )
        
        # Load your LoRA adapter from FineTunedModel - THIS MUST WORK!
        model.load_adapter("../FineTunedModel", adapter_name="emergency")
        
        # Ensure tokenizer has pad token
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            
        logger.info("✅ Fine-tuned model with LoRA loaded successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Fine-tuned model loading FAILED: {e}")
        logger.error("❌ NO FALLBACKS - Fix the LoRA loading issue!")
        
        # Reset globals to None
        model = None
        tokenizer = None
        return False

def classify_emergency(text: str) -> str:
    """Classify emergency text - Using RAW tokenizer approach like working Gemma server"""
    global model, tokenizer
    
    if model is None or tokenizer is None:
        raise RuntimeError("Model not loaded")
    
    try:
        logger.info(f"Classifying text: '{text}'")
        
        # Create prompt exactly like training
        prompt = f"Classify this emergency into one of these categories: {CATEGORIES_STR}\n\nEmergency: {text}\n\nCategory:"
        
        # Use RAW tokenizer approach (like your working Gemma server)
        messages = [{
            "role": "user",
            "content": [{"type": "text", "text": prompt}]
        }]
        
        # Apply chat template using RAW tokenizer (WORKING approach)
        inputs = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(model.device)
        
        logger.info(f"Tokenization successful, shape: {inputs['input_ids'].shape}")
        
        # Generate with same params as your working server
        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=5,
                do_sample=False,  # Greedy for consistent results
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        
        logger.info(f"Generation successful, shape: {outputs.shape}")
        
        # Decode response - same as working server
        response = tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[-1]:], 
            skip_special_tokens=True
        ).strip()
        
        logger.info(f"Raw response: '{response}'")
        
        # Extract category - same logic as test.py
        response_lower = response.lower()
        for category in CATEGORIES:
            if category in response_lower:
                logger.info(f"Found category: {category}")
                return category
        
        # Fallback
        fallback = response_lower.split()[0] if response_lower else "unknown"
        logger.info(f"Using fallback: {fallback}")
        return fallback
        
    except Exception as e:
        logger.error(f"Classification error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return "error"

def get_model_info():
    """Get model information"""
    return {
        "model_loaded": model is not None,
        "categories": CATEGORIES,
        "model_path": "../FineTunedModel (LoRA)",
        "device": str(model.device) if model else "not_loaded"
    }

# Emergency Report Functions

def save_emergency_image_to_gcs(report_id: str, image_data: bytes, filename: str) -> Optional[str]:
    """Save emergency image to GCS and return the path"""
    try:
        client = storage.Client()
        bucket = client.bucket(EMERGENCY_BUCKET)
        
        # Create unique filename
        file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
        blob_name = f"{EMERGENCY_IMAGES_PREFIX}{report_id}_{int(time.time())}.{file_extension}"
        
        blob = bucket.blob(blob_name)
        blob.upload_from_string(
            image_data,
            content_type=f'image/{file_extension}'
        )
        
        gcs_path = f"gs://{EMERGENCY_BUCKET}/{blob_name}"
        print(f"✅ Emergency image saved to GCS: {gcs_path}")
        return gcs_path
        
    except Exception as e:
        print(f"❌ Error saving emergency image to GCS: {e}")
        return None

def send_emergency_email(report_data: dict, image_gcs_path: Optional[str] = None) -> bool:
    """Send emergency report email with image attachment"""
    try:
        if not EMAIL_PASSWORD:
            print("⚠️ Email password not set. Cannot send emergency alert.")
            return False
            
        print(f"📧 Sending emergency alert email for report {report_data['report_id']}...")
        
        # Create email message
        msg = EmailMessage()
        msg["Subject"] = f"🚨 EMERGENCY REPORT - {report_data['classification'].upper()} - {report_data['location']}"
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        
        # Build email body
        body_lines = [
            f"🚨 EMERGENCY REPORT ALERT 🚨",
            f"",
            f"📍 Location: {report_data['location']}",
            f"🆔 Report ID: {report_data['report_id']}",
            f"🏷️ AI Classification: {report_data['classification'].upper()}",
            f"⏰ Reported At: {report_data['timestamp']}",
            f"",
            f"📝 EMERGENCY DESCRIPTION:",
            f"{report_data['message']}",
            f"",
            f"📞 Contact: {report_data.get('contact', 'Not provided')}",
            f"",
            f"🤖 AI ANALYSIS DETAILS:",
            f"├── Category: {get_category_description(report_data['classification'])}",
            f"├── Analysis Time: {report_data.get('analysis_time', 'N/A')}s",
            f"├── Confidence: High (Emergency Classification System)",
            f"└── Priority: {get_priority_level(report_data['classification'])}",
            f"",
        ]
        
        if image_gcs_path:
            body_lines.extend([
                f"📷 IMAGE ATTACHMENT:",
                f"Emergency photo has been attached to this email.",
                f"GCS Path: {image_gcs_path}",
                f"",
            ])
        
        body_lines.extend([
            f"⚠️ IMMEDIATE ACTION REQUIRED!",
            f"",
            f"This emergency report has been automatically classified by our AI system.",
            f"Please verify the situation and dispatch appropriate emergency response.",
            f"",
            f"📊 Response Guidelines:",
            f"• CHILD_LOST: Immediate search and security alert",
            f"• MEDICAL_HELP: Dispatch medical team immediately", 
            f"• CROWD_PANIC: Deploy crowd control measures",
            f"• SMALL_FIRE: Alert fire safety team",
            f"• NEED_INTERPRETER: Send multilingual support",
            f"• LOST_ITEM: Standard lost & found procedure",
            f"",
            f"This alert was generated by Gemma Kavach Emergency System"
        ])
        
        msg.set_content("\n".join(body_lines))
        
        # Attach image if available
        if image_gcs_path and report_data.get('image_data'):
            try:
                image_data = report_data['image_data']
                classification = report_data['classification']
                filename = f"emergency_{classification}_{report_data['report_id']}.jpg"
                
                msg.add_attachment(
                    image_data,
                    maintype="image",
                    subtype="jpeg",
                    filename=filename
                )
                print(f"✅ Image attached to email: {filename}")
            except Exception as e:
                print(f"⚠️ Failed to attach image: {e}")
        
        # Send email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
            
        print(f"✅ Emergency alert email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send emergency email: {e}")
        return False

def get_category_description(classification: str) -> str:
    """Get human-readable description for classification"""
    descriptions = {
        'child_lost': 'Missing Child - High Priority Search Required',
        'crowd_panic': 'Crowd Control Emergency - Panic Situation Detected',
        'lost_item': 'Lost Property - Standard Recovery Procedure',
        'medical_help': 'Medical Emergency - Immediate Medical Attention Required',
        'need_interpreter': 'Language Assistance - Interpreter Support Needed',
        'small_fire': 'Fire Emergency - Fire Safety Response Required'
    }
    return descriptions.get(classification, f'Unknown Classification: {classification}')

def get_priority_level(classification: str) -> str:
    """Get priority level for classification"""
    priority_levels = {
        'child_lost': 'CRITICAL',
        'crowd_panic': 'CRITICAL', 
        'medical_help': 'HIGH',
        'small_fire': 'HIGH',
        'need_interpreter': 'MEDIUM',
        'lost_item': 'LOW'
    }
    return priority_levels.get(classification, 'MEDIUM')

def generate_report_id() -> str:
    """Generate unique emergency report ID"""
    timestamp = int(time.time())
    random_part = str(uuid.uuid4())[:8].upper()
    return f"EMG-{timestamp}-{random_part}"

def get_current_timestamp() -> str:
    """Get current timestamp in readable format"""
    return time.strftime("%Y-%m-%d %H:%M:%S")