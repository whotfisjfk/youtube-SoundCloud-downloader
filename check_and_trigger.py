import os
import requests
import hashlib
from pathlib import Path

LOG_URL = "https://raw.githubusercontent.com/alipoorkaramali/youtube-news-watcher/main/logs/new_videos.txt"
STATE_FILE = "processed.txt"

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
    قالب جدید خط:
    timestamp | platform | title (می‌تواند شامل | باشد) | relative_time | url | pub_date_iran
    با rsplit(" | ", 2) سه بخش از راست جدا می‌شود:
    بخش‌های قبل از relative_time، relative_time، url|date
    اما در واقع rsplit با maxsplit=2 از راست دو بار تقسیم می‌کند:
    جداکننده بین url و date → ['بقیه خط تا قبل از date', 'date']
    سپس جداکننده بین relative_time و url → ['بقیه خط تا قبل از relative_time', 'url', 'date']
    بنابراین خروجی: ['بقیه خط', 'relative_time', 'url', 'date'] نیست بلکه سه عضوی است: ['بقیه خط', 'url', 'date']؟
    آزمایش ذهنی: "A | B | C | D | E | F" rsplit(" | ", 2)
    مرحله اول: جدا از راست → بین E و F => ["A | B | C | D | E", "F"]
    مرحله دوم: جدا از راست روی رشته اول → بین D و E => ["A | B | C | D", "E", "F"]
    پس خروجی نهایی: ["A | B | C | D", "E", "F"]  که E=url, F=date
    پس url در اندیس ۱ است.
    """
    parts = line.rsplit(" | ", 2)
    if len(parts) == 3:
        url_candidate = parts[1].strip()
        if url_candidate.startswith("https://www.youtube.com/watch") or url_candidate.startswith("https://soundcloud.com/"):
            return url_candidate
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
    platform = "youtube" if "youtube.com" in video_url else "soundcloud"
    payload = {
        "ref": "main",
        "inputs": {
            "platform": platform,
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
