import os
import requests
import hashlib
from pathlib import Path

# آدرس فایل لاگ در مخزن دوم – توجه به مسیر logs/new_videos.txt
LOG_URL = "https://raw.githubusercontent.com/alipoorkaramali/youtube-news-watcher/main/logs/new_videos.txt"

# فایل محلی برای ردگیری لینک‌های پردازش‌شده
STATE_FILE = "processed.txt"

# اطلاعات مخزن اول برای فراخوانی workflow دانلود
REPO_OWNER = "alipoorkaramali"
REPO_NAME = "youtube-SoundCloud-downloader"
WORKFLOW_FILE = "Multi-Platform Downloader.yml"  # نام دقیق فایل workflow
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

def get_processed():
    """برگرداندن مجموعه‌ای از هش لینک‌هایی که قبلاً پردازش شده‌اند"""
    if not Path(STATE_FILE).exists():
        return set()
    with open(STATE_FILE) as f:
        return set(line.strip() for line in f if line.strip())

def save_processed(hashes):
    """ذخیرهٔ هش‌های جدید در فایل وضعیت"""
    with open(STATE_FILE, "w") as f:
        for h in hashes:
            f.write(h + "\n")

def extract_url(line: str) -> str | None:
    """
    خط به فرمت:
    timestamp | title | relative time | url
    آخرین بخش (بعد از آخرین |) لینک یوتیوب است.
    """
    parts = line.split(" | ")
    if len(parts) >= 4:
        url = parts[-1].strip()
        if url.startswith("https://www.youtube.com/watch"):
            return url
    return None

def trigger_download(video_url: str):
    """اجرای workflow دانلود از طریق GitHub API (workflow_dispatch)"""
    url = (
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
        f"/actions/workflows/{WORKFLOW_FILE}/dispatches"
    )
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "ref": "main",
        "inputs": {
            "url": video_url   # باید با نام پارامتر در workflow دانلود تطابق داشته باشد
        }
    }
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code == 204:
        print(f"✅ دانلود آغاز شد: {video_url}")
    else:
        print(f"❌ خطا برای {video_url}: {resp.status_code} {resp.text}")

def main():
    # ۱. دریافت فایل لاگ از مخزن دوم
    resp = requests.get(LOG_URL)
    if resp.status_code != 200:
        print(f"⚠️ دریافت لاگ ناموفق: {resp.status_code}")
        return

    lines = [line.strip() for line in resp.text.splitlines() if line.strip()]
    processed_hashes = get_processed()
    new_hashes = []

    # ۲. پردازش هر خط و استخراج لینک
    for line in lines:
        video_url = extract_url(line)
        if not video_url:
            print(f"⚠️ نتوانستم لینکی از خط زیر استخراج کنم:\n{line}")
            continue

        # هش لینک برای ردگیری (بدون تکرار)
        link_hash = hashlib.md5(video_url.encode()).hexdigest()
        if link_hash in processed_hashes:
            continue

        # ۳. فراخوانی دانلودر برای لینک جدید
        trigger_download(video_url)
        processed_hashes.add(link_hash)
        new_hashes.append(link_hash)

    # ۴. ذخیرهٔ وضعیت جدید اگر لینک جدیدی وجود داشت
    if new_hashes:
        save_processed(processed_hashes)
        print(f"🎉 {len(new_hashes)} ویدیوی جدید پردازش شد.")
    else:
        print("🔄 ویدیوی جدیدی برای پردازش وجود ندارد.")

if __name__ == "__main__":
    main()
