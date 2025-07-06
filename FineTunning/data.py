from pydantic import BaseModel
from typing import Literal
from google import genai
import os
import pandas as pd
import json
import time
from dotenv import load_dotenv

load_dotenv()

# Define the data models for each emergency class
class ChildLostSample(BaseModel):
    text: str
    label: Literal["child_lost"]

class CrowdPanicSample(BaseModel):
    text: str
    label: Literal["crowd_panic"]

class LostItemSample(BaseModel):
    text: str
    label: Literal["lost_item"]

class MedicalHelpSample(BaseModel):
    text: str
    label: Literal["medical_help"]

class NeedInterpreterSample(BaseModel):
    text: str
    label: Literal["need_interpreter"]

class SmallFireSample(BaseModel):
    text: str
    label: Literal["small_fire"]

# Set up Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Define prompts for each class with examples
PROMPTS = {
    "child_lost": {
        "model": ChildLostSample,
        "prompt": """You are an emergency data generator for a crowd management system.

Generate 100 realistic examples of people reporting lost children in Hinglish (Hindi-English mix). Each example should be natural, urgent, and different from others. Use common Indian expressions and situations.

Examples of existing data:
- "Bacha kho gaya hai"
- "Ek chota ladka dikh nahi raha"
- "Mummy bacha gum ho gaya"
- "Zone D me ek child nahi mil raha"
- "Koi bacha ro raha tha akela"

Generate varied scenarios like:
- Parents looking for lost children
- Children separated from families
- Lost children crying alone
- Specific descriptions of missing children
- Urgent pleas for help finding children

Return only JSON array format:
[
  {"text": "example text", "label": "child_lost"},
  ...
]"""
    },
    
    "crowd_panic": {
        "model": CrowdPanicSample,
        "prompt": """You are an emergency data generator for a crowd management system.

Generate 100 realistic examples of people reporting crowd panic situations in Hinglish (Hindi-English mix). Each example should be natural, urgent, and different from others.

Examples of existing data:
- "Log bhaag rahe hain"
- "Bahut bheed hai"
- "Panic mach gaya hai"
- "Sab log dhakka de rahe hain"
- "People running everywhere"

Generate varied scenarios like:
- Stampede situations
- Overcrowding reports
- Panic spreading in crowds
- People pushing and shoving
- Chaotic crowd behavior

Return only JSON array format:
[
  {"text": "example text", "label": "crowd_panic"},
  ...
]"""
    },
    
    "lost_item": {
        "model": LostItemSample,
        "prompt": """You are an emergency data generator for a crowd management system.

Generate 100 realistic examples of people reporting lost items in Hinglish (Hindi-English mix). Each example should be natural and different from others.

Examples of existing data:
- "Mera bag kho gaya"
- "Wallet nahi mil raha"
- "Mobile chhoot gaya"
- "Kisi ne mera saman utha liya"
- "Watch kho gaya"

Generate varied scenarios like:
- Lost personal belongings
- Misplaced items
- Stolen items
- Items left behind
- Valuable items missing

Return only JSON array format:
[
  {"text": "example text", "label": "lost_item"},
  ...
]"""
    },
    
    "medical_help": {
        "model": MedicalHelpSample,
        "prompt": """You are an emergency data generator for a crowd management system.

Generate 100 realistic examples of people requesting medical help in Hinglish (Hindi-English mix). Each example should be natural, urgent, and different from others.

Examples of existing data:
- "Inko doctor chahiye"
- "Banda behosh ho gaya hai"
- "Patient ko turant madad chahiye"
- "Yahan ek aadmi zameen par gira hua hai"
- "Khoon nikal raha hai kisi ke pair se"

Generate varied scenarios like:
- Medical emergencies
- Accidents and injuries
- People fainting or collapsing
- Need for ambulance/doctor
- First aid requirements

Return only JSON array format:
[
  {"text": "example text", "label": "medical_help"},
  ...
]"""
    },
    
    "need_interpreter": {
        "model": NeedInterpreterSample,
        "prompt": """You are an emergency data generator for a crowd management system.

Generate 100 realistic examples of people needing interpreter/translation help in Hinglish (Hindi-English mix). Each example should be natural and different from others.

Examples of existing data:
- "Tourist ko help chahiye"
- "Kisi ko translator chahiye"
- "Tourist ko unka group nahi mil raha"
- "Foreigner samaj nahi paa raha"
- "Guide bhejo yahan"

Generate varied scenarios like:
- Foreign tourists needing help
- Language barriers
- Lost tourists
- Communication problems
- Need for guides/translators

Return only JSON array format:
[
  {"text": "example text", "label": "need_interpreter"},
  ...
]"""
    },
    
    "small_fire": {
        "model": SmallFireSample,
        "prompt": """You are an emergency data generator for a crowd management system.

Generate 100 realistic examples of people reporting small fires in Hinglish (Hindi-English mix). Each example should be natural, urgent, and different from others.

Examples of existing data:
- "Aag lag gayi hai"
- "Khana ke stall ke paas smoke aa raha hai"
- "Fire ho gaya yahan"
- "Dhuaa dikh raha hai"
- "Stall ke paas kuch jal raha hai"

Generate varied scenarios like:
- Small fires at food stalls
- Smoke detection
- Electrical fires
- Cooking accidents
- Small burning incidents

Return only JSON array format:
[
  {"text": "example text", "label": "small_fire"},
  ...
]"""
    }
}

def load_existing_data(class_name):
    """Load existing data for a class if it exists"""
    filename = f"{class_name}_progress.csv"
    try:
        if os.path.exists(filename):
            df = pd.read_csv(filename)
            print(f"📂 Found existing data for {class_name}: {len(df)} samples")
            return df.to_dict('records')
        else:
            print(f"📝 No existing data found for {class_name}, starting fresh")
            return []
    except Exception as e:
        print(f"⚠️ Error loading existing data for {class_name}: {e}")
        return []

def save_intermediate_data(class_name, samples):
    """Save intermediate data for a class"""
    filename = f"{class_name}_progress.csv"
    try:
        df = pd.DataFrame(samples)
        df.to_csv(filename, index=False)
        print(f"💾 Saved intermediate data: {filename} ({len(samples)} samples)")
    except Exception as e:
        print(f"❌ Error saving intermediate data for {class_name}: {e}")

def generate_batch(class_name, batch_num, total_batches):
    """Generate 100 samples for a specific class"""
    print(f"Generating batch {batch_num}/{total_batches} for {class_name}...")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite-preview-06-17",
            contents=PROMPTS[class_name]["prompt"],
            config={
                "response_mime_type": "application/json",
                "response_schema": list[PROMPTS[class_name]["model"]],
                "temperature": 0.9,  # Increased for more variety with larger dataset
            },
        )
        
        samples = response.parsed
        print(f"✅ Generated {len(samples)} samples for {class_name} (batch {batch_num}/{total_batches})")
        return samples
        
    except Exception as e:
        print(f"❌ Error generating batch {batch_num} for {class_name}: {e}")
        return []

def generate_class_data(class_name):
    """Generate 10,000 samples for a specific class (100 batches of 100 each)"""
    print(f"\n🔄 Starting generation for {class_name}...")
    
    # Load existing data if any
    class_samples = load_existing_data(class_name)
    current_count = len(class_samples)
    
    # Calculate how many batches we still need
    target_samples = 10000  # Updated to 10K per class for 2B model
    samples_needed = target_samples - current_count
    batches_needed = max(0, (samples_needed + 99) // 100)  # Round up
    total_batches = 100  # Total batches needed for 10K samples
    
    if current_count >= target_samples:
        print(f"✅ {class_name} already has {current_count} samples (target: {target_samples})")
        return class_samples[:target_samples]  # Return only the first 10K
    
    print(f"📊 Current: {current_count}, Target: {target_samples}, Need: {samples_needed} more samples")
    print(f"🎯 Will generate {batches_needed} more batches")
    
    # Calculate starting batch number
    completed_batches = current_count // 100
    start_batch = completed_batches + 1
    
    # Generate remaining batches
    for batch_num in range(start_batch, start_batch + batches_needed):
        try:
            batch_samples = generate_batch(class_name, batch_num, total_batches)
            
            if batch_samples:
                # Add new samples to existing data
                class_samples.extend([s.dict() for s in batch_samples])
                
                # Save intermediate progress every 10 batches or at end
                if batch_num % 10 == 0 or batch_num == start_batch + batches_needed - 1:
                    save_intermediate_data(class_name, class_samples)
                
                print(f"📈 Progress: {len(class_samples)}/{target_samples} samples for {class_name} ({len(class_samples)/target_samples*100:.1f}%)")
            else:
                print(f"⚠️ No samples generated in batch {batch_num}, continuing...")
            
            # Add shorter delay for large dataset generation
            time.sleep(1)
            
        except KeyboardInterrupt:
            print(f"\n🛑 Generation interrupted for {class_name}")
            print(f"💾 Saved progress: {len(class_samples)} samples")
            save_intermediate_data(class_name, class_samples)
            break
        except Exception as e:
            print(f"❌ Unexpected error in batch {batch_num}: {e}")
            continue
    
    # Ensure we don't exceed target
    class_samples = class_samples[:target_samples]
    
    print(f"✅ Completed {class_name}: {len(class_samples)} total samples")
    
    # Save final class file
    df = pd.DataFrame(class_samples)
    final_filename = f"{class_name}_10000.csv"
    df.to_csv(final_filename, index=False)
    print(f"💾 Saved final file: {final_filename}")
    
    return class_samples

def cleanup_progress_files():
    """Clean up intermediate progress files"""
    classes = ["child_lost", "crowd_panic", "lost_item", "medical_help", "need_interpreter", "small_fire"]
    
    print("\n🧹 Cleaning up intermediate files...")
    for class_name in classes:
        progress_file = f"{class_name}_progress.csv"
        if os.path.exists(progress_file):
            try:
                os.remove(progress_file)
                print(f"🗑️ Removed {progress_file}")
            except Exception as e:
                print(f"⚠️ Could not remove {progress_file}: {e}")

def main():
    """Main function to run the data generation"""
    print("🚀 Starting Emergency Data Generation")
    print("=" * 60)
    print("Target: 10,000 samples per class (6 classes total = 60,000)")
    print("Method: 100 batches of 100 samples each per class")
    print("Model: gemini-2.5-flash-lite-preview-06-17")
    print("Optimized for: 2B parameter model fine-tuning")
    print("Features: ✅ Resume support ✅ Intermediate saves")
    print("=" * 60)
    
    # List of all classes to generate
    classes = ["child_lost", "crowd_panic", "lost_item", "medical_help", "need_interpreter", "small_fire"]
    
    all_data = {}
    
    try:
        # Generate data for each class
        for class_name in classes:
            class_samples = generate_class_data(class_name)
            all_data[class_name] = class_samples
        
        # Create summary
        print("\n📊 GENERATION SUMMARY:")
        print("=" * 60)
        
        total_samples = 0
        for class_name, samples in all_data.items():
            count = len(samples)
            total_samples += count
            print(f"{class_name:20}: {count:4d} samples")
        
        print("=" * 60)
        print(f"{'TOTAL':20}: {total_samples:4d} samples")
        
        # Create combined dataset
        print("\n📦 Creating combined dataset...")
        combined_data = []
        for class_name, samples in all_data.items():
            combined_data.extend(samples)
        
        combined_df = pd.DataFrame(combined_data)
        combined_df.to_csv("emergency_dataset_60000.csv", index=False)
        print(f"💾 Saved combined dataset: emergency_dataset_60000.csv")
        
        # Show class distribution in combined dataset
        print("\n📈 Class Distribution in Combined Dataset:")
        print("-" * 40)
        class_counts = combined_df['label'].value_counts()
        for class_name, count in class_counts.items():
            print(f"{class_name:20}: {count:4d}")
        
        print("\n🎉 Data generation completed successfully!")
        print(f"Files generated:")
        for class_name in classes:
            print(f"   - {class_name}_10000.csv")
        print(f"   - emergency_dataset_60000.csv")
        
        # Calculate dataset statistics for training
        total_tokens_approx = total_samples * 25  # Assume ~25 tokens per sample
        print(f"\n📊 Training Statistics for 2B Model:")
        print(f"   - Total samples: {total_samples:,}")
        print(f"   - Estimated tokens: {total_tokens_approx:,}")
        print(f"   - Token/Parameter ratio: {total_tokens_approx/2_000_000_000:.6f}")
        print(f"   - Recommended training steps: 3,000-5,000")
        print(f"   - Suggested batch size: 4-8")
        print(f"   - Estimated training time: 2-4 hours on A100")
        
        # Ask if user wants to clean up progress files
        print(f"\nProgress files (*_progress.csv) are still available for resume capability.")
        cleanup_choice = input("Do you want to clean up progress files? (y/n): ").lower()
        if cleanup_choice in ['y', 'yes']:
            cleanup_progress_files()
        else:
            print("📁 Progress files kept for future resume capability")
            
    except KeyboardInterrupt:
        print(f"\n🛑 Generation interrupted by user")
        print(f"💾 All progress has been saved in *_progress.csv files")
        print(f"🔄 Run the script again to resume from where you left off")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print(f"💾 All progress has been saved in *_progress.csv files")
        print(f"🔄 Run the script again to resume from where you left off")

if __name__ == "__main__":
    main()