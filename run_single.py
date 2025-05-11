import os
import shutil
from analyzer_module import analyze_pdf

# === הגדרות בסיסיות להפעלה ===
file_path = "116000039.pdf"   # מיקום הקובץ שתרצה לנתח
dry_run = False                             # True = רק לבדיקה, לא שומר למסד
show_data = True                            # True = מציג את הנתונים במסך

# === הרצת הניתוח בפועל ===
result = analyze_pdf(file_path, dry_run=dry_run, show_data=show_data)
print(result)

# === אם הצליח ואין dry_run – שאל את המשתמש אם להעביר ===
if result.startswith("✅") and not dry_run:
    user_input = input("האם להעביר את הקובץ לתיקיית 'processed'? [y/N]: ")
    move_to_processed = user_input.strip().lower() in ("y", "yes", "כן", "j")

    if move_to_processed:
        os.makedirs("processed", exist_ok=True)
        dest_path = os.path.join("processed", os.path.basename(file_path))
        shutil.move(file_path, dest_path)
        print(f"📁 הקובץ הועבר לתיקיית processed: {dest_path}")
    else:
        print("ℹ️ הקובץ נשאר בתיקיית המקור.")


