import os
from datetime import datetime, timezone, timedelta

FOLDER = "audio_downloads"          # پوشه‌ای که فایل‌های خودکار در آن ذخیره می‌شوند
TIMES_FILE = "upload_times.txt"
MAX_HOURS = 12

now = datetime.now(timezone.utc)
cutoff = now - timedelta(hours=MAX_HOURS)

# خواندن زمان‌های ثبت‌شده
entries = []
if os.path.exists(TIMES_FILE):
    with open(TIMES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if " | " in line:
                fname, time_str = line.split(" | ", 1)
                entries.append((fname, time_str))

kept_entries = []
files_deleted = 0

for fname, time_str in entries:
    try:
        file_time = datetime.fromisoformat(time_str)
    except:
        kept_entries.append((fname, time_str))
        continue

    file_path = os.path.join(FOLDER, fname)

    if os.path.exists(file_path) and file_time < cutoff:
        os.remove(file_path)
        files_deleted += 1
        print(f"🗑️ حذف شد: {fname} (ثبت‌شده در {time_str})")
    else:
        kept_entries.append((fname, time_str))

# بازنویسی فایل upload_times.txt با فایل‌های باقی‌مانده
with open(TIMES_FILE, "w", encoding="utf-8") as f:
    for fname, time_str in kept_entries:
        f.write(f"{fname} | {time_str}\n")

if files_deleted == 0:
    print("✅ هیچ فایل قدیمی‌ای برای حذف وجود نداشت.")
else:
    print(f"✅ {files_deleted} فایل قدیمی حذف شدند.")
