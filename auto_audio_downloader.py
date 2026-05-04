import os
import subprocess
import requests
import hashlib
from pathlib import Path

LOG_URL = "https://raw.githubusercontent.com/alipoorkaramali/youtube-news-watcher/main/logs/new_videos.txt"
STATE_FILE = "processed_audio.txt"
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

def extract_info(line):
    """
    با استفاده از rsplit از سمت راست، url و پلتفرم را به صورت امن استخراج می‌کند.
    """
    parts = line.rsplit(" | ", 3)
    if len(parts) < 4:
        return None, None
    url = parts[-1].strip()
    # پلتفرم را از بخش‌های ابتدایی حدس می‌زنیم
    platform = "youtube" if "youtube.com" in url else "soundcloud"
    return platform, url

def download_audio(platform, url):
    Path(DEST_FOLDER).mkdir(parents=True, exist_ok=True)

    if platform == "youtube":
        cmd = [
            "yt-dlp",
            "-f", "bestaudio[ext=m4a]/bestaudio/best",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "--cookies", "cookies.txt",
            "--force-overwrites",
            "--no-playlist",
            url,
            "-o", f"{DEST_FOLDER}/%(title)s.%(ext)s"
        ]
    else:  # soundcloud
        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "--no-playlist",
            "--force-ipv4",
            url,
            "-o", f"{DEST_FOLDER}/%(title)s.%(ext)s"
        ]
    print(f"⬇️ دانلود صوت {platform}: {url}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ دانلود موفق")
    else:
        print(f"❌ خطا در دانلود:\n{result.stderr}")

def main():
    resp = requests.get(LOG_URL)
    if resp.status_code != 200:
        print(f"⚠️ دریافت لاگ ناموفق: {resp.status_code}")
        return

    lines = [line.strip() for line in resp.text.splitlines() if line.strip()]
    processed = get_processed()
    new_hashes = []

    for line in lines:
        plat, url = extract_info(line)
        if not url:
            print(f"⚠️ نتوانستم لینکی از خط زیر استخراج کنم:\n{line}")
            continue
        h = hashlib.md5(url.encode()).hexdigest()
        if h in processed:
            continue
        download_audio(plat, url)
        processed.add(h)
        new_hashes.append(h)

    if new_hashes:
        save_processed(processed)
        print(f"🎉 {len(new_hashes)} فایل صوتی جدید دانلود شد.")
    else:
        print("🔄 فایل جدیدی برای دانلود وجود ندارد.")

if __name__ == "__main__":
    main()
