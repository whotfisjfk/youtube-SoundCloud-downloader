import os
import subprocess
import requests
import hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone

LOG_URL = "https://raw.githubusercontent.com/alipoorkaramali/youtube-news-watcher/main/logs/new_videos.txt"
STATE_FILE = "processed_audio.txt"
DEST_FOLDER = "audio_downloads"

def iran_offset():
    now = datetime.now()
    return timedelta(hours=4, minutes=30) if 3 <= now.month <= 9 else timedelta(hours=3, minutes=30)

def iran_tz():
    return timezone(iran_offset())

def iran_now():
    return datetime.now(timezone.utc) + iran_offset()

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
    قالب خط: timestamp | platform | title | relative_time | url | pub_date_iran
    pub_date_iran به فرمت YYYY-MM-DD
    خروجی: (platform, url, pub_date_str) یا (None, None, None) در صورت خطا
    """
    parts = line.rsplit(" | ", 2)
    if len(parts) != 3:
        return None, None, None
    url_candidate = parts[1].strip()
    if not (url_candidate.startswith("https://www.youtube.com/watch") or url_candidate.startswith("https://soundcloud.com/")):
        return None, None, None
    pub_date = parts[2].strip()
    plat = "youtube" if "youtube.com" in url_candidate else "soundcloud"
    return plat, url_candidate, pub_date

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

    today_iran_str = iran_now().strftime("%Y-%m-%d")

    for line in lines:
        plat, url, pub_date = extract_info(line)
        if not url or not pub_date:
            print(f"⚠️ نتوانستم اطلاعات لازم را از خط زیر استخراج کنم:\n{line}")
            continue

        # فقط فایل‌های مربوط به امروز ایران
        if pub_date != today_iran_str:
            print(f"⏩ رد شد (تاریخ {pub_date} ≠ امروز {today_iran_str}): {url}")
            continue

        h = hashlib.md5(url.encode()).hexdigest()
        if h in processed:
            continue

        download_audio(plat, url)
        processed.add(h)
        new_hashes.append(h)

    if new_hashes:
        save_processed(processed)
        print(f"🎉 {len(new_hashes)} فایل صوتی جدید (مربوط به امروز) دانلود شد.")
    else:
        print("🔄 فایل جدیدی برای امروز وجود ندارد.")

if __name__ == "__main__":
    main()
