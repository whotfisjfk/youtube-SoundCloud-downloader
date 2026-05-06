import os
import time
from pathlib import Path

DEST_FOLDER = "audio_downloads"
MAX_AGE_HOURS = 24

def cleanup_old_files():
    folder = Path(DEST_FOLDER)
    if not folder.exists():
        print(f"📁 پوشهٔ {DEST_FOLDER} وجود ندارد. پاک‌سازی انجام نشد.")
        return

    now = time.time()
    cutoff_time = now - MAX_AGE_HOURS * 3600  # ۲۴ ساعت قبل به ثانیه

    deleted_count = 0
    for file_path in folder.iterdir():
        if file_path.is_file():
            mtime = file_path.stat().st_mtime  # زمان آخرین تغییر فایل
            if mtime < cutoff_time:
                print(f"🗑️ در حال حذف فایل قدیمی: {file_path.name}")
                file_path.unlink()
                deleted_count += 1

    if deleted_count == 0:
        print("✅ هیچ فایل قدیمی‌تری برای حذف یافت نشد.")
    else:
        print(f"🎯 {deleted_count} فایل قدیمی (بیشتر از {MAX_AGE_HOURS} ساعت) حذف شد.")

if __name__ == "__main__":
    cleanup_old_files()
