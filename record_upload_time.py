import sys
import os
from datetime import datetime, timezone

FOLDER = sys.argv[1]           # پوشه‌ای که فایل‌ها در آن دانلود شده‌اند
TIMES_FILE = "upload_times.txt"

# خواندن فایل زمان‌های موجود (اگر هست) و نگهداشتن خطوط مربوط به فایل‌هایی که هنوز وجود دارند
existing = {}
if os.path.exists(TIMES_FILE):
    with open(TIMES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if " | " in line:
                fname, time_str = line.split(" | ", 1)
                existing[fname] = time_str

# اضافه کردن فایل‌های جدیدی که در پوشه هستند
now_iso = datetime.now(timezone.utc).isoformat()
new_entries = []
for fname in os.listdir(FOLDER):
    if fname in existing:
        continue
    new_entries.append(f"{fname} | {now_iso}")

# بازنویسی فایل با ترکیب فایل‌های موجود و جدید
with open(TIMES_FILE, "w", encoding="utf-8") as f:
    # ابتدا فایل‌هایی که قبلاً ثبت شده و هنوز وجود دارند
    for fname, t in existing.items():
        if os.path.exists(os.path.join(FOLDER, fname)):
            f.write(f"{fname} | {t}\n")
    # سپس فایل‌های جدید
    for entry in new_entries:
        f.write(entry + "\n")
