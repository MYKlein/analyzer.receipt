# batch_analyzer.py

import os
import shutil
from analyzer_module import analyze_pdf

def process_folder(
    folder_path: str,
    dry_run: bool = False,
    move_processed: bool = True,
    processed_dir: str = "processed"
):
    """
    מעבד את כל קבצי ה‑PDF שבתיקייה folder_path:
      • dry_run=True  – רק מציג תוצאות, לא שומר למסד ולא מעביר קבצים.
      • move_processed=True – לאחר הצלחה (✅) מעביר את ה‑PDF לתיקיית processed_dir.
    בסוף מדפיס סיכום ויוצר process_log.txt בתוך folder_path.
    """
    # ודא שתיקיית processed קיימת
    os.makedirs(processed_dir, exist_ok=True)

    total = inserted = skipped = errors = 0
    log_lines = []

    for fname in os.listdir(folder_path):
        if not fname.lower().endswith(".pdf"):
            continue
        total += 1
        full_path = os.path.join(folder_path, fname)
        result = analyze_pdf(full_path, dry_run=dry_run)
        print(result)
        log_lines.append(result)

        if result.startswith("✅"):
            inserted += 1
            if move_processed and not dry_run:
                shutil.move(full_path, os.path.join(processed_dir, fname))
        elif result.startswith("⚠️") or result.startswith("🧪"):
            skipped += 1
        else:
            errors += 1

    # סיכום
    summary = [
        "\n--- סיכום מתוך process_folder ---",
        f"סה\"כ קבצים: {total}",
        f"{'יוזנו למסד' if not dry_run else 'נותחו בלבד'}: {inserted}",
        f"כבר היו במסד / דולגו: {skipped}",
        f"שגיאות: {errors}"
    ]
    print("\n".join(summary))

    # כתיבת לוג
    log_path = os.path.join(folder_path, "process_log.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines + summary))


if __name__ == "__main__":
    # ריצה ישירה: מעבד את התיקייה pdf_receipts
    process_folder(
      folder_path="pdf_receipts",
      dry_run=False,
      move_processed=True,
      processed_dir="processed"
    )
