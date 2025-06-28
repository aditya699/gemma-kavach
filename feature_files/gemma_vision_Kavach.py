import os
import uuid
import json
import shutil
import asyncio
import aiohttp
import smtplib
import imageio
from PIL import Image, ImageDraw
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

# ------------------ CONFIG ------------------
API_URL            = "https://nsl6up9ztcem6h-8000.proxy.runpod.net/ask_image"
FRAME_DIR          = "extracted_frames"
ALERT_DIR          = "alerts"
PROMPT             = (
    "Analyze this image carefully. Do you see any signs of a stampede or crowd panic — "
    "such as people tightly packed, pushing, running, falling, or any chaos in the scene? "
    "Reply 'Yes' if any such signs are visible. Otherwise, reply 'No' only."
)
EMAIL_SENDER       = "ab0358031@gmail.com"
EMAIL_PASSWORD     = os.getenv("GOOGLE_APP_PASSWORD")
EMAIL_RECEIVER     = "ab0358031@gmail.com"
MAX_CONCURRENT     = 10  # Adjust based on API rate limits
# --------------------------------------------

def get_verdict(score_percent: float) -> str:
    """Map risk percentage to verdict."""
    if score_percent <= 10:
        return "SAFE"
    elif score_percent <= 30:
        return "WATCH"
    else:
        return "ALERT"

def save_flagged_frames(event_id, flagged_frames):
    """Copy flagged frames to an alerts directory for record-keeping."""
    output_path = os.path.join(ALERT_DIR, f"event_{event_id}")
    os.makedirs(output_path, exist_ok=True)
    for frame in flagged_frames:
        src = os.path.join(FRAME_DIR, frame["frame"])
        dst = os.path.join(output_path, frame["frame"])
        shutil.copyfile(src, dst)
    return output_path

def generate_heatmap_gif(event_dir, flagged_frames, total_frames):
    """Generate a GIF overlaying a warning banner on flagged frames."""
    print("🎞️ Generating heat-map GIF...")
    flagged_set = {f["frame"] for f in flagged_frames}
    gif_frames = []
    for i in range(total_frames):
        fname = f"frame_{i:02d}.jpg"
        path = os.path.join(event_dir, fname)
        if not os.path.exists(path):
            continue
        img = Image.open(path).convert("RGB")
        if fname in flagged_set:
            draw = ImageDraw.Draw(img)
            draw.rectangle([(0, 0), (img.width, 40)], fill=(255, 0, 0))
            draw.text((10, 10), "⚠️ Stampede Risk", fill="white")
        gif_frames.append(img)
    gif_path = os.path.join(event_dir, "summary.gif")
    imageio.mimsave(gif_path, gif_frames, fps=1)
    print(f"✅ Saved GIF: {gif_path}")

def send_email(event_id, result, frame_dir):
    """Send an email alert with the risk summary and all flagged frames attached."""
    msg = EmailMessage()
    msg["Subject"] = f"🚨 ALERT: Crowd Panic Detected (Event {event_id})"
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = EMAIL_RECEIVER

    # Build email body
    lines = [
        f"Event ID: {event_id}",
        f"Verdict: {result['verdict']}",
        f"Risk Score: {result['risk_score_percent']}%",
        "Flagged Frames:",
        "Location: Mela Zone A"
    ]
    for f in result["flagged_frames"]:
        lines.append(f" - {f['timestamp']} → {f['frame']}")
    lines.append("\nPlease investigate immediately.")
    msg.set_content("\n".join(lines))

    # Attach flagged images
    for f in result["flagged_frames"]:
        img_path = os.path.join(frame_dir, f["frame"])
        with open(img_path, "rb") as img:
            msg.add_attachment(img.read(),
                               maintype="image",
                               subtype="jpeg",
                               filename=f["frame"])
    # Attach GIF
    gif_path = os.path.join(frame_dir, "summary.gif")
    if os.path.exists(gif_path):
        with open(gif_path, "rb") as gif:
            msg.add_attachment(gif.read(),
                               maintype="image",
                               subtype="gif",
                               filename="summary.gif")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print("📧 Email sent successfully!")
    except Exception as e:
        print(f"⚠️ Failed to send email: {e}")

async def analyze_single_frame(session, filename, index):
    """Analyze a single frame asynchronously."""
    ts = f"00:{index:02d}"
    path = os.path.join(FRAME_DIR, filename)
    
    try:
        with open(path, "rb") as f:
            image_data = f.read()
        
        # Create form data for multipart/form-data request
        data = aiohttp.FormData()
        data.add_field('image', image_data, filename=filename, content_type='image/jpeg')
        data.add_field('prompt', PROMPT)
        
        print(f"📤 Sending {filename} (timestamp {ts})...")
        
        async with session.post(API_URL, data=data) as response:
            response.raise_for_status()
            result = await response.json()
            text = result.get("text", "").strip().lower()
            print(f"🧠 Response for {filename}: {text}")
            
            if text == "yes":
                return {
                    "frame": filename,
                    "timestamp": ts,
                    "response": "Yes"
                }
            else:
                return None
                
    except Exception as e:
        print(f"⚠️ Error on {filename}: {e}")
        return None

async def analyze_frames():
    """Main async function to analyze all frames."""
    event_id = str(uuid.uuid4())[:8]
    
    # Get all image files
    image_files = [f for f in sorted(os.listdir(FRAME_DIR)) 
                   if f.lower().endswith(".jpg")]
    total_frames = len(image_files)
    
    if total_frames == 0:
        print("No image files found in the frame directory!")
        return
    
    # Create semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    
    async def analyze_with_semaphore(session, filename, index):
        async with semaphore:
            return await analyze_single_frame(session, filename, index)
    
    # Create aiohttp session with timeout
    timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout per request
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Create tasks for all frames
        tasks = [
            analyze_with_semaphore(session, filename, i)
            for i, filename in enumerate(image_files)
        ]
        
        print(f"🚀 Starting analysis of {total_frames} frames with max {MAX_CONCURRENT} concurrent requests...")
        
        # Execute all tasks and gather results
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    flagged_frames = []
    error_count = 0
    
    for result in results:
        if isinstance(result, Exception):
            error_count += 1
            print(f"⚠️ Task failed with exception: {result}")
        elif result is not None:  # Frame was flagged
            flagged_frames.append(result)
    
    # Compute risk
    yes_count = len(flagged_frames)
    score_percent = round((yes_count / total_frames) * 100, 2) if total_frames else 0.0
    verdict = get_verdict(score_percent)

    result_summary = {
        "event_id": event_id,
        "verdict": verdict,
        "risk_score_percent": score_percent,
        "yes_count": yes_count,
        "total_frames": total_frames,
        "error_count": error_count,
        "flagged_frames": flagged_frames
    }

    # Save JSON audit log
    frame_dir = save_flagged_frames(event_id, flagged_frames)
    with open(os.path.join(frame_dir, "result.json"), "w") as jf:
        json.dump(result_summary, jf, indent=2)

    # Generate heat-map GIF
    generate_heatmap_gif(frame_dir, flagged_frames, total_frames)

    # Send email if ALERT
    if verdict == "ALERT":
        send_email(event_id, result_summary, frame_dir)

    # Print summary to console
    print("\n📊 Final Risk Analysis:")
    print(json.dumps(result_summary, indent=2))

def main():
    """Entry point that runs the async analysis."""
    try:
        asyncio.run(analyze_frames())
    except KeyboardInterrupt:
        print("\n⏹️ Analysis interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()