import os
import requests
import hashlib
from pathlib import Path

# آدرس فایل لاگ در مخزن دوم
LOG_URL = "https://raw.githubusercontent.com/alipoorkaramali/youtube-news-watcher/main/logs/new_videos.txt"

# فایل محلی برای ردگیری لینک‌های پردازش‌شده
STATE_FILE = "processed.txt"

# اطلاعات مخزن اول برای فراخوانی workflow
REPO_OWNER = "alipoorkaramali"
REPO_NAME = "youtube-SoundCloud-downloader"
WORKFLOW_FILE = "Multi-Platform Downloader.yml"
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

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
    """
    خطوط به یکی از این دو فرمت هستند:
    1. قدیمی (یوتیوب): timestamp | title | rel_time | url
    2. جدید (ساندکلاد): timestamp | platform | title (ممکن است خود شامل | باشد) | rel_time | url
    برای استخراج امن، از rsplit با محدودیت ۳ بار تقسیم از سمت راست استفاده می‌کنیم
    تا url و rel_time جدا شوند و مابقی خط (که شامل title است) دست‌نخورده باقی بماند.
    """
    parts = line.rsplit(" | ", 3)  # حداکثر ۳ بار از سمت راست تقسیم می‌کند
    if len(parts) == 4:
        # آخرین بخش همیشه URL است
        url = parts[-1].strip()
        # بخش سوم rel_time است
        relative_time = parts[-2].strip()
        # تمام بخش‌های قبلی (timestamp [| platform] | title) هستند
        # چک می‌کنیم که URL معتبر باشد
        if url.startswith("https://www.youtube.com/watch") or url.startswith("https://soundcloud.com/"):
            return url
    return None

def trigger_download(video_url: str):
    workflow_id = requests.utils.quote(WORKFLOW_FILE, safe='')
    url = (
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
        f"/actions/workflows/{workflow_id}/dispatches"
    )
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "ref": "main",
        "inputs": {
            "platform": "youtube" if "youtube.com" in video_url else "soundcloud",
            "url": video_url,
            "format": "audio",
            "folder": "downloads"
        }
    }
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code == 204:
        print(f"✅ دانلود آغاز شد: {video_url}")
    else:
        print(f"❌ خطا برای {video_url}: {resp.status_code} {resp.text}")

def main():
    resp = requests.get(LOG_URL)
    if resp.status_code != 200:
        print(f"⚠️ دریافت لاگ ناموفق: {resp.status_code}")
        return

    lines = [line.strip() for line in resp.text.splitlines() if line.strip()]
    processed_hashes = get_processed()
    new_hashes = []

    for line in lines:
        video_url = extract_url(line)
        if not video_url:
            print(f"⚠️ نتوانستم لینکی از خط زیر استخراج کنم:\n{line}")
            continue

        link_hash = hashlib.md5(video_url.encode()).hexdigest()
        if link_hash in processed_hashes:
            continue

        trigger_download(video_url)
        processed_hashes.add(link_hash)
        new_hashes.append(link_hash)

    if new_hashes:
        save_processed(processed_hashes)
        print(f"🎉 {len(new_hashes)} ویدیوی جدید پردازش شد.")
    else:
        print("🔄 ویدیوی جدیدی برای پردازش وجود ندارد.")

if __name__ == "__main__":
    main()
