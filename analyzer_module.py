import pdfplumber
import sqlite3
import re

# חילוץ הטקסט מתוך קובץ PDF
def extract_text(file_path):
    with pdfplumber.open(file_path) as pdf:
        return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

# חילוץ ערך בודד לפי regex
# חילוץ ערך בודד לפי regex כולל ניקוי פסיקים ומינוס בסוף
def extract_field(pattern, text):
    match = re.search(pattern, text)
    if match:
        value = match.group(1).strip()

        # הסרת פסיקים מהמספר (למשל: 1,097.38 → 1097.38)
        value = value.replace(",", "")

        # טיפול במקרה של מינוס בסוף (למשל: 57.76- → -57.76)
        if value.endswith("-"):
            value = "-" + value[:-1]

        return value
    return None


# חילוץ כל השדות הרלוונטיים
def extract_fields(text):
    return {
        "document_id": extract_field(r"(\d+)\s*\(םימולשת לע חוד\)\s*הלבק", text),
        "invoice_id": extract_field(r"(\d+)\s*:רפסמ ךמסמ - ןיכומיס", text),
        "date": extract_field(r"(\d{2}\.\d{2}\.\d{4})\s*:םולשת ךיראת", text),

        "taxable_income": extract_field(
            r"([\d,]+\.\d+)\s*:\(םיפיט\s+אלל\)\s*מ\"?עמב\s+תובייח\s+תוסנכה", text
        ),
        "tips": extract_field(
            r"([\d\,]+\.\d+)\s*:\s*מ[\"״”]?עמ\s+ללוכ\s+אל\s+םיפיט", text
        ),

        # משתמשים באותו ביטוי לשניהם, כמו שביקשת
        "amount_total": extract_field(
            r"(\d+\.\d+)\s*:תוסנכה\s+כ.?\"?הס", text
        ),
        "total_income": extract_field(
            r"([\d,]+\.\d+)\s*:תוסנכה\s+כ.?\"?הס", text
        ),

        "deduction": extract_field(r"(-?[\d,]+\.\d+)\s*:יוכינה\s+םוכס", text),
        "summary" : extract_field(r"([\d,]+\.\d+)\s*:\s*םייניב םוכיס", text),
        "final_amount": extract_field(r"([\d,]+\.\d+)\s*:םולשתל\s+יפוס\s+םוכס", text),

        "vendor": extract_field(r":םלשמה יטרפ\s*(.+)", text),
        "internal_vendor_id": extract_field(r"(\d+)\s*:ימינפ\s+קפס\s+רפסמ", text),

        # מחזיר רק את התאריך הראשון מתוך טווח (בלי multi)
        "billing_cycle": extract_field(r"(\d{2}\.\d{2}\.\d{4})\s*—\s*\d{2}\.\d{2}\.\d{4}\s*:בויח רוזחמ", text),

        "raw_text": text
    }

# בדיקה אם הקבלה כבר במסד
def document_exists(document_id):
    conn = sqlite3.connect("receipts_v2.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM receipts WHERE document_id = ?", (document_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

# שמירה למסד הנתונים
def save_to_db(data):
    conn = sqlite3.connect("receipts_v2.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO receipts (
            document_id,
            invoice_id,
            date,
            taxable_income,
            tips,
            total_income,
            amount_total,
            deduction,
            summary,
            final_amount,
            vendor,
            internal_vendor_id,
            billing_cycle,
            raw_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["document_id"],
        data["invoice_id"],
        data["date"],
        data["taxable_income"],
        data["tips"],
        data["total_income"],
        data["amount_total"],
        data["deduction"],
        data["summary"],
        data["final_amount"],
        data["vendor"],
        data["internal_vendor_id"],
        data["billing_cycle"],
        data["raw_text"]
    ))

    conn.commit()
    conn.close()

# הפונקציה הראשית לניתוח קובץ PDF
def analyze_pdf(file_path, dry_run=False, show_data=False ):
    try:
        text = extract_text(file_path)
        data = extract_fields(text)

        if not data["document_id"]:
            return f"❌ {file_path} – אין document_id, נדחה."


        # אם למסמך יש מזהה , יודפסו הקריטריונים שנדרשו למסד
        if show_data:
            print("\n📋 נתונים שנותחו מתוך הקובץ:")
            print("קבלה (דוח על תשלומים):", data["document_id"])
            print("הכנסות חייבות במע\"מ (ללא טיפים):", data["taxable_income"])
            print("טיפים לא כולל מע\"מ:", data["tips"])
            print("סה\"כ הכנסות 1 :", data["amount_total"])
            print("סה\"כ הכנסות:", data["total_income"])
            print("סכום הניכויים:", data["deduction"])
            print("סיכום ביניים:", data["summary"])
            print("סכום סופי לתשלום:", data["final_amount"])
            print("תאריך תשלום:", data["date"])
            print("פרטי המשלם:", data["vendor"])
            print("מספר ספק פנימי:", data["internal_vendor_id"])
            print("מחזור חיוב:", data["billing_cycle"])
            print("סימוכין - מסמך מספר:", data["invoice_id"])
            print("-" * 40)


        if document_exists(data["document_id"]):
            return f"⚠️ {file_path} – כבר קיים במסד, לא נוסף."

        if not dry_run:
            save_to_db(data)
            return f"✅ {file_path} – נשמר בהצלחה למסד."
        else:
            return f"🧪 {file_path} – מצב בדיקה בלבד (לא נשמר)."

    except Exception as e:
        return f"❌ {file_path} – שגיאה: {str(e)}"
