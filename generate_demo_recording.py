import sys
import os
import time
import threading
from pathlib import Path
import httpx
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(r"C:\Users\sushant\.gemini\antigravity\scratch\ai-career-assistant")
sys.path.insert(0, str(PROJECT_ROOT))

VIDEO_DIR = PROJECT_ROOT / "demo_video"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_PDF = PROJECT_ROOT / "data" / "sample_resume.pdf"

# Clean old webm files
for f in VIDEO_DIR.glob("*.webm"):
    try: f.unlink()
    except Exception: pass

print("=" * 60, flush=True)
print("STARTING AUTOMATED DEMO VIDEO RECORDING PIPELINE", flush=True)
print("=" * 60, flush=True)

# 1. Start FastAPI server in background
import uvicorn
from backend.app.main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()

server_ready = False
for _ in range(30):
    try:
        r = httpx.get("http://127.0.0.1:8000/api/health", timeout=1.0)
        if r.status_code == 200:
            server_ready = True
            print("✓ FastAPI server is ready.", flush=True)
            break
    except Exception:
        time.sleep(0.5)

if not server_ready:
    print("Server failed to start.", flush=True)
    sys.exit(1)

# 2. Launch Playwright
print("[Step 2] Launching Playwright Chromium in 1920x1080...", flush=True)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        record_video_dir=str(VIDEO_DIR),
        record_video_size={"width": 1920, "height": 1080}
    )
    page = context.new_page()
    page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
    time.sleep(2)

    # SCENE 1: Resume Upload
    print("[Scene 1] Uploading Resume PDF...", flush=True)
    page.locator('input[type="file"]').set_input_files(str(SAMPLE_PDF))
    page.wait_for_selector('text=Identified Technical Skills', timeout=20000)
    time.sleep(2.5)
    
    # Toggle text inspection
    try:
        btn = page.locator('button:has-text("View Extracted Text")')
        if btn.is_visible(timeout=3000):
            btn.click()
            time.sleep(2)
            btn.click()
            time.sleep(1)
    except Exception as e:
        print(f"Note on view text: {e}", flush=True)

    # SCENE 2: Job Match Analysis
    print("[Scene 2] Job Match Analysis...", flush=True)
    page.locator('button:has-text("2. Job Match Analysis")').click()
    time.sleep(1.5)
    page.locator('button:has-text("Generative AI / LLM Engineer")').click()
    time.sleep(1)
    page.locator('button:has-text("Analyze Match")').click()
    page.wait_for_selector('text=Resume-JD Match Breakdown', timeout=20000)
    time.sleep(2.5)
    page.evaluate("window.scrollBy({ top: 350, behavior: 'smooth' });")
    time.sleep(2.5)
    page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' });")
    time.sleep(1)

    # SCENE 3: RAG Chat
    print("[Scene 3] RAG Resume Chat...", flush=True)
    page.locator('button:has-text("3. RAG Resume Chat")').click()
    time.sleep(1.5)
    page.locator('button:has-text("What projects have I done using AWS?")').click()
    time.sleep(3)
    try:
        src_btn = page.locator('button:has-text("Retrieved Context")').first
        if src_btn.is_visible(timeout=2000):
            src_btn.click()
            time.sleep(2.5)
    except Exception:
        pass

    chat_input = page.locator('input[placeholder="Ask a question about the resume..."]')
    chat_input.fill("What AWS certifications does the candidate have?")
    time.sleep(1)
    chat_input.press("Enter")
    time.sleep(3)

    # SCENE 4: Interview Prep
    print("[Scene 4] Interview Question Generation...", flush=True)
    page.locator('button:has-text("4. Interview Prep")').click()
    time.sleep(1.5)
    page.locator('button:has-text("Generate Questions")').click()
    page.wait_for_selector('text=Generated Questions', timeout=20000)
    time.sleep(2.5)
    try:
        star_btn = page.locator('button:has-text("✨ Generate STAR Answer")').first
        if star_btn.is_visible(timeout=3000):
            star_btn.click()
            time.sleep(3.5)
    except Exception:
        pass
    page.evaluate("window.scrollBy({ top: 250, behavior: 'smooth' });")
    time.sleep(2)
    page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' });")
    time.sleep(1)

    # SCENE 5: Resume Polish
    print("[Scene 5] Resume Polish & Bullet Point Enhancer...", flush=True)
    page.locator('button:has-text("5. Resume Polish")').click()
    time.sleep(1.5)
    page.locator('button:has-text("Analyze Resume Quality")').click()
    page.wait_for_selector('text=Key Resume Strengths', timeout=20000)
    time.sleep(2.5)
    page.evaluate("window.scrollBy({ top: 400, behavior: 'smooth' });")
    time.sleep(1.5)
    page.locator('button:has-text("✨ Rewrite Bullet Point")').click()
    page.wait_for_selector('text=Impact-Driven Rewritten Bullet', timeout=20000)
    time.sleep(3.5)
    page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' });")
    time.sleep(2)

    print("[Step 3] Finalizing video file...", flush=True)
    video_path_obj = page.video.path()
    context.close()
    browser.close()

final_video_path = VIDEO_DIR / "ai_career_assistant_demo.webm"
if os.path.exists(video_path_obj):
    if final_video_path.exists():
        final_video_path.unlink()
    os.rename(video_path_obj, str(final_video_path))
    print(f"\n✓ Final Demo Video generated at:\n  {final_video_path}", flush=True)
    print(f"  File size: {round(os.path.getsize(final_video_path) / (1024 * 1024), 2)} MB", flush=True)

print("=" * 60, flush=True)
print("DEMO RECORDING SUCCEEDED!", flush=True)
print("=" * 60, flush=True)
