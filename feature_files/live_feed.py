import cv2
import os
import uuid
import json
import shutil
import asyncio
import aiohttp
import smtplib
import imageio
import time
from PIL import Image, ImageDraw
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

# ------------------ CONFIG ------------------
API_URL            = "https://nsl6up9ztcem6h-8000.proxy.runpod.net/ask_image"
PROMPT             = (
    "Analyze this image carefully. Do you see any signs of a stampede or crowd panic — "
    "such as people tightly packed, pushing, running, falling, or any chaos in the scene? "
    "Reply 'Yes' if any such signs are visible. Otherwise, reply 'No' only."
)
TEMP_DIR           = "stream_frames"
ALERT_DIR          = "alerts"
EMAIL_SENDER       = "ab0358031@gmail.com"
EMAIL_PASSWORD     = os.getenv("GOOGLE_APP_PASSWORD")
EMAIL_RECEIVER     = "ab0358031@gmail.com"
MAX_CONCURRENT     = 3  # Lower for real-time processing
FRAME_INTERVAL     = 1  # seconds between captures
FRAME_LIMIT        = 8 # Stop after N frames (or use ESC to exit)
# --------------------------------------------

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(ALERT_DIR, exist_ok=True)

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
        src = os.path.join(TEMP_DIR, frame["frame"])
        dst = os.path.join(output_path, frame["frame"])
        if os.path.exists(src):
            shutil.copyfile(src, dst)
    return output_path

def generate_heatmap_gif(event_dir, flagged_frames, total_frames, event_id):
    """Generate a GIF overlaying a warning banner on flagged frames."""
    print("🎞️ Generating heat-map GIF...")
    flagged_set = {f["frame"] for f in flagged_frames}
    gif_frames = []
    
    for i in range(total_frames):
        fname = f"frame_{i:02d}.jpg"
        # Check in both temp dir and event dir
        path = os.path.join(event_dir, fname)
        if not os.path.exists(path):
            path = os.path.join(TEMP_DIR, fname)
        if not os.path.exists(path):
            continue
            
        img = Image.open(path).convert("RGB")
        if fname in flagged_set:
            draw = ImageDraw.Draw(img)
            draw.rectangle([(0, 0), (img.width, 40)], fill=(255, 0, 0))
            draw.text((10, 10), "⚠️ Stampede Risk", fill="white")
        gif_frames.append(img)
    
    if gif_frames:
        gif_path = os.path.join(event_dir, "summary.gif")
        imageio.mimsave(gif_path, gif_frames, fps=1)
        print(f"✅ Saved GIF: {gif_path}")
        return gif_path
    return None

def send_email(event_id, result, frame_dir):
    """Send an email alert with the risk summary and all flagged frames attached."""
    if not EMAIL_PASSWORD:
        print("⚠️ Email password not set. Skipping email notification.")
        return
        
    msg = EmailMessage()
    msg["Subject"] = f"🚨 ALERT: Crowd Panic Detected (Event {event_id})"
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = EMAIL_RECEIVER

    # Build email body
    lines = [
        f"Event ID: {event_id}",
        f"Verdict: {result['verdict']}",
        f"Risk Score: {result['risk_score_percent']}%",
        f"Total Frames Analyzed: {result['total_frames']}",
        f"Flagged Frames: {result['yes_count']}",
        "",
        "Flagged Frame Details:",
    ]
    for f in result["flagged_frames"]:
        lines.append(f" - {f['timestamp']} → {f['frame']}")
    lines.append("\n⚠️ Please investigate immediately!")
    msg.set_content("\n".join(lines))

    # Attach flagged images
    for f in result["flagged_frames"]:
        img_path = os.path.join(frame_dir, f["frame"])
        if os.path.exists(img_path):
            with open(img_path, "rb") as img:
                msg.add_attachment(img.read(),
                                   maintype="image",
                                   subtype="jpeg",
                                   filename=f["frame"])
    
    # Attach GIF if it exists
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
        print("📧 Email alert sent successfully!")
    except Exception as e:
        print(f"⚠️ Failed to send email: {e}")

async def analyze_frame(frame_path, timestamp, session, semaphore):
    """Analyze a single frame asynchronously."""
    async with semaphore:
        try:
            with open(frame_path, "rb") as f:
                img_data = f.read()
            
            data = aiohttp.FormData()
            data.add_field('image', img_data, filename=os.path.basename(frame_path), content_type='image/jpeg')
            data.add_field('prompt', PROMPT)
            
            async with session.post(API_URL, data=data) as resp:
                resp.raise_for_status()
                result = await resp.json()
                text = result.get("text", "").strip().lower()
                
                status = "🔴 RISK" if text == "yes" else "🟢 SAFE"
                print(f"🧠 [{timestamp}] → {status}")
                
                return text == "yes"
        except Exception as e:
            print(f"❌ Frame {timestamp} error: {e}")
            return False

def process_results(flagged_frames, total_frames, event_id):
    """Process analysis results and take appropriate actions."""
    yes_count = len(flagged_frames)
    score_percent = round((yes_count / total_frames) * 100, 2) if total_frames else 0.0
    verdict = get_verdict(score_percent)

    result = {
        "event_id": event_id,
        "verdict": verdict,
        "risk_score_percent": score_percent,
        "yes_count": yes_count,
        "total_frames": total_frames,
        "flagged_frames": flagged_frames,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Save flagged frames and generate reports
    if flagged_frames:
        frame_dir = save_flagged_frames(event_id, flagged_frames)
        
        # Save JSON audit log
        with open(os.path.join(frame_dir, "result.json"), "w") as jf:
            json.dump(result, jf, indent=2)
        
        # Generate heat-map GIF
        generate_heatmap_gif(frame_dir, flagged_frames, total_frames, event_id)
        
        # Send email if ALERT
        if verdict == "ALERT":
            send_email(event_id, result, frame_dir)
    
    return result

async def main():
    """Main function for real-time crowd monitoring."""
    event_id = str(uuid.uuid4())[:8]
    flagged_frames = []
    frame_count = 0
    last_capture = time.time()
    
    # Create semaphore and session for API calls
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    timeout = aiohttp.ClientTimeout(total=10)  # Shorter timeout for real-time
    
    print(f"📹 Starting Real-time Crowd Monitor (Event ID: {event_id})")
    print(f"📸 Capturing every {FRAME_INTERVAL} seconds, max {FRAME_LIMIT} frames")
    print("⌨️  Press ESC to exit early.\n")
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Error: Could not open camera")
        return
    
    # Store pending analysis tasks
    pending_tasks = []
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            while cap.isOpened() and frame_count < FRAME_LIMIT:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Failed to capture frame")
                    break

                now = time.time()
                
                # Capture frame at intervals
                if now - last_capture >= FRAME_INTERVAL:
                    ts = f"{frame_count:02d}"
                    frame_path = os.path.join(TEMP_DIR, f"frame_{ts}.jpg")
                    cv2.imwrite(frame_path, frame)
                    
                    print(f"📸 Captured frame_{ts}.jpg")
                    
                    # Start async analysis
                    task = asyncio.create_task(
                        analyze_frame(frame_path, ts, session, semaphore)
                    )
                    pending_tasks.append((task, ts, f"frame_{ts}.jpg"))
                    
                    frame_count += 1
                    last_capture = now
                
                # Check completed analysis tasks
                completed_tasks = []
                for i, (task, timestamp, filename) in enumerate(pending_tasks):
                    if task.done():
                        completed_tasks.append(i)
                        try:
                            is_risky = await task
                            if is_risky:
                                flagged_frames.append({
                                    "timestamp": timestamp,
                                    "frame": filename,
                                    "response": "Yes"
                                })
                                print(f"🚨 Frame {timestamp} flagged as risky!")
                        except Exception as e:
                            print(f"❌ Task error for {timestamp}: {e}")
                
                # Remove completed tasks
                for i in reversed(completed_tasks):
                    pending_tasks.pop(i)
                
                # Display live feed with status overlay
                status_text = f"Event: {event_id} | Frames: {frame_count}/{FRAME_LIMIT} | Flagged: {len(flagged_frames)}"
                cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                if flagged_frames:
                    cv2.putText(frame, "⚠️ RISK DETECTED", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                
                cv2.imshow("Live Crowd Monitor", frame)
                
                # Exit on ESC key
                if cv2.waitKey(1) & 0xFF == 27:
                    print("\n⏹️ Monitoring stopped by user")
                    break
                
                # Small delay to prevent excessive CPU usage
                await asyncio.sleep(0.01)
            
            # Wait for any remaining tasks to complete
            if pending_tasks:
                print(f"⏳ Waiting for {len(pending_tasks)} remaining analysis tasks...")
                for task, timestamp, filename in pending_tasks:
                    try:
                        is_risky = await task
                        if is_risky:
                            flagged_frames.append({
                                "timestamp": timestamp,
                                "frame": filename,
                                "response": "Yes"
                            })
                    except Exception as e:
                        print(f"❌ Final task error for {timestamp}: {e}")
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
    
    # Process final results
    print("\n📊 Processing final results...")
    result = process_results(flagged_frames, frame_count, event_id)
    
    # Display final summary
    print("\n" + "="*50)
    print("📊 FINAL CROWD ANALYSIS REPORT")
    print("="*50)
    print(f"Event ID: {event_id}")
    print(f"Verdict: {result['verdict']}")
    print(f"Risk Score: {result['risk_score_percent']}%")
    print(f"Flagged Frames: {result['yes_count']} / {result['total_frames']}")
    
    if flagged_frames:
        print("\n🚨 Flagged Frames:")
        for frame in flagged_frames:
            print(f"  - {frame['timestamp']} → {frame['frame']}")
        
        if result['verdict'] == "ALERT":
            print(f"\n📧 Email alert sent to {EMAIL_RECEIVER}")
        
        print(f"\n📁 Files saved to: alerts/event_{event_id}/")
    else:
        print("\n✅ No risk detected during monitoring session")
    
    print("\n🧹 Cleaning up temporary files...")
    try:
        shutil.rmtree(TEMP_DIR)
        print("✅ Cleanup complete")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Monitoring interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        # Ensure camera is released
        cv2.destroyAllWindows()