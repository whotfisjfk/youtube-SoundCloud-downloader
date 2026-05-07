import os
import subprocess
import requests
import hashlib
from pathlib import Path

LOG_URL = "https://raw.githubusercontent.com/alipoorkaramali/youtube-news-watcher/main/logs/new_videos.txt"
STATE_FILE = "processed_audio.txt"
TITLE_STATE_FILE = "processed_titles.txt"          # جدید: ذخیره‌سازی عناوین دانلودشده
DEST_FOLDER = "audio_downloads"

def get_processed():
    """خواندن هش لینک‌های قبلاً پردازش‌شده"""
    if not Path(STATE_FILE).exists():
        return set()
    with open(STATE_FILE) as f:
        return set(line.strip() for line in f if line.strip())

def save_processed(hashes):
    """ذخیرهٔ هش لینک‌ها"""
    with open(STATE_FILE, "w") as f:
        for h in hashes:
            f.write(h + "\n")

def load_processed_titles():
    """خواندن عناوینی که قبلاً دانلود شده‌اند"""
    if not Path(TITLE_STATE_FILE).exists():
        return set()
    with open(TITLE_STATE_FILE, encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())

def add_processed_title(title):
    """افزودن یک عنوان به فایل و مجموعهٔ عناوین پردازش‌شده"""
    with open(TITLE_STATE_FILE, "a", encoding='utf-8') as f:
        f.write(title + "\n")

def parse_log_line(line):
    """
    استخراج ایمن platform و عنوان کامل از خط لاگ.
    ساختار خط:
    timestamp | platform | عنوان (ممکن است شامل | باشد) | relative_time | url
    """
    parts = line.split(" | ")
    if len(parts) < 4:
        return None, None, None

    # پلتفرم همیشه در ایندکس ۱ است
    platform = parts[1].strip()
    if platform not in ("youtube", "soundcloud"):
        # ممکن است پلتفرم درست نباشد؛ با url حدس می‌زنیم
        url = parts[-1].strip()
        platform = "youtube" if "youtube.com" in url else "soundcloud" if "soundcloud.com" in url else None
        return platform, None, url

    # url همیشه آخرین بخش است
    url = parts[-1].strip()

    # عنوان = تمام بخش‌های بین ایندکس ۲ تا یکی مانده به آخر (چون بخش آخر url است)
    # اما بخش یکی مانده به آخر relative_time است (مثل "0 minutes ago")
    # پس عنوان = parts[2:-1] و اگر بیش از یک بخش بود با " | " به هم می‌چسبانیم
    title_parts = parts[2:-1]
    if not title_parts:
        title = None
    else:
        title = " | ".join(title_parts).strip()

    return platform, title, url

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
        return True
    else:
        print(f"❌ خطا در دانلود:\n{result.stderr}")
        return False

def main():
    resp = requests.get(LOG_URL)
    if resp.status_code != 200:
        print(f"⚠️ دریافت لاگ ناموفق: {resp.status_code}")
        return

    lines = [line.strip() for line in resp.text.splitlines() if line.strip()]
    processed_urls = get_processed()
    processed_titles = load_processed_titles()

    new_downloads = 0

    for line in lines:
        plat, title, url = parse_log_line(line)
        if not url:
            print(f"⚠️ نتوانستم لینکی از خط زیر استخراج کنم:\n{line}")
            continue

        # ۱. بررسی تکراری بودن لینک (فعالیت قبلی)
        url_hash = hashlib.md5(url.encode()).hexdigest()
        if url_hash in processed_urls:
            continue

        # ۲. بررسی تکراری بودن عنوان (جدید)
        if title and title in processed_titles:
            print(f"⏭️ عنوان تکراری از منبع دیگر: {title}")
            # باز هم لینک را به عنوان دیده‌شده علامت می‌زنیم که دوباره بررسی نشود
            processed_urls.add(url_hash)
            continue

        # دانلود
        success = download_audio(plat, url)
        if success:
            # ذخیره در مجموعهٔ لینک‌ها و عناوین
            processed_urls.add(url_hash)
            if title:
                processed_titles.add(title)
                add_processed_title(title)
            new_downloads += 1
        else:
            # حتی در صورت شکست، لینک را علامت می‌زنیم تا در اجراهای بعدی تکرار نشود
            processed_urls.add(url_hash)

    # ذخیره نهایی هش‌های لینک (عنوان‌ها بلافاصله append شده‌اند)
    save_processed(processed_urls)

    if new_downloads:
        print(f"🎉 {new_downloads} فایل صوتی جدید دانلود شد.")
    else:
        print("🔄 فایل جدیدی برای دانلود وجود ندارد.")

if __name__ == "__main__":
    main()
