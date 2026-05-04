import os
import subprocess
import requests
import hashlib
from pathlib import Path

# آدرس فایل لاگ در مخزن دوم
LOG_URL = "https://raw.githubusercontent.com/alipoorkaramali/youtube-news-watcher/main/logs/new_videos.txt"

# فایل محلی برای ردگیری لینک‌های پردازش‌شده
STATE_FILE = "processed_audio.txt"

# پوشه‌ای که فایل‌های صوتی در آن ذخیره می‌شوند
DEST_FOLDER = "audio_downloads"

def get_processed():
    if not Path(STATE_FILE).exists():
        return set()
    with open(STATE_FILE) as f:
        return set(line.strip() for line in f if line.strip())

def save_processed(hashes):
    with open(STATE_FILE, "w") as f:
        for h in hashes:
            f.write(h + "\n")

def extract_url(line: str) -> str | None:
    parts = line.split(" | ")
    if len(parts) >= 4:
        url = parts[-1].strip()
        if url.startswith("https://www.youtube.com/watch"):
            return url
    return None

def download_audio(video_url: str):
    """دانلود صوت از یوتیوب با yt-dlp (خروجی MP3)"""
    Path(DEST_FOLDER).mkdir(parents=True, exist_ok=True)
    # استفاده از همان دستور موجود در ورک‌فلوی اصلی برای صوت یوتیوب
    cmd = [
        "yt-dlp",
        "-f", "bestaudio[ext=m4a]/bestaudio/best",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--cookies", "cookies.txt",
        "--force-overwrites",
        "--no-playlist",
        video_url,
        "-o", f"{DEST_FOLDER}/%(title)s.%(ext)s"
    ]
    print(f"⬇️ در حال دانلود صوت: {video_url}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ دانلود موفق")
    else:
        print(f"❌ خطا در دانلود:\n{result.stderr}")

def main():
    # ۱. دریافت فایل لاگ
    resp = requests.get(LOG_URL)
    if resp.status_code != 200:
        print(f"⚠️ دریافت لاگ ناموفق: {resp.status_code}")
        return

    lines = [line.strip() for line in resp.text.splitlines() if line.strip()]
    processed = get_processed()
    new_hashes = []

    for line in lines:
        url = extract_url(line)
        if not url:
            continue
        h = hashlib.md5(url.encode()).hexdigest()
        if h in processed:
            continue
        download_audio(url)
        processed.add(h)
        new_hashes.append(h)

    if new_hashes:
        save_processed(processed)
        print(f"🎉 {len(new_hashes)} فایل صوتی جدید دانلود شد.")
    else:
        print("🔄 فایل جدیدی برای دانلود وجود ندارد.")

if __name__ == "__main__":
    main()
