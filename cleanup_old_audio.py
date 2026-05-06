import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

DEST_FOLDER = "audio_downloads"
MAX_AGE_HOURS = 24

def get_git_commit_timestamp(file_path):
    """
    دریافت timestamp آخرین commit فایل با استفاده از git log.
    اگر فایل در Git نباشد یا خطایی رخ دهد، None برمی‌گرداند.
    """
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%at", "--", str(file_path)],
            capture_output=True,
            text=True,
            check=True
        )
        ts = result.stdout.strip()
        if ts:
            return int(ts)
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        pass
    return None

def cleanup_old_files():
    folder = Path(DEST_FOLDER)
    if not folder.exists():
        print(f"📁 پوشهٔ {DEST_FOLDER} وجود ندارد. پاک‌سازی انجام نشد.")
        return

    now = datetime.now(timezone.utc).timestamp()
    cutoff_time = now - MAX_AGE_HOURS * 3600

    deleted_count = 0
    for file_path in folder.iterdir():
        if not file_path.is_file():
            continue

        commit_ts = get_git_commit_timestamp(file_path)
        if commit_ts is None:
            print(f"⚠️ نمی‌توان timestamp کامیت {file_path.name} را خواند. نادیده گرفته شد.")
            continue

        if commit_ts < cutoff_time:
            print(f"🗑️ در حال حذف فایل قدیمی: {file_path.name} (آخرین commit: {datetime.fromtimestamp(commit_ts, tz=timezone.utc)})")
            file_path.unlink()
            # ثبت عملیات حذف در Git
            subprocess.run(["git", "add", str(file_path)], capture_output=True)
            deleted_count += 1

    if deleted_count == 0:
        print("✅ هیچ فایل قدیمی‌تری برای حذف یافت نشد.")
    else:
        print(f"🎯 {deleted_count} فایل قدیمی (بیشتر از {MAX_AGE_HOURS} ساعت از آخرین commit) حذف و برای کامیت آماده شد.")

if __name__ == "__main__":
    cleanup_old_files()
