import pdfplumber
import sqlite3
import re

# פתח את קובץ ה-PDF
with pdfplumber.open("116000040.pdf") as pdf:

    text = ''
    for page in pdf.pages:
        text += page.extract_text()
print(text)

# חילוץ נתונים מהטקסט
def extract_field(pattern, text):
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None

# חילוץ נתונים עם regex מותאמים לפי סדר RTL אמיתי מתוך PDF
invoice_id = extract_field(r"(\d+)\s*:רפסמ ךמסמ - ןיכומיס", text)
date = extract_field(r"(\d{2}\.\d{2}\.\d{4})\s*:םולשת ךיראת", text)
deduction = extract_field(r"(-?[\d,]+\.\d+)\s*:יוכינה\s+םוכס", text)
final_amount = extract_field(r"(\d+\.\d+)\s*:םולשתל יפוס םוכס", text)
vendor = (extract_field(r":םלשמה יטרפ\s*(.+)", text))




# שדות נוספים שביקשת
document_id = extract_field(r"(\d+)\s*\(םימולשת לע חוד\) הלבק", text)
taxable_income = extract_field(r"(\d+\.\d+)\s*:\(םיפיט אלל\)\s*\מ\"עמב\s+תובייח\s+תוסנכה", text)
tips = extract_field(r"([\d\.]+)\s*:\s*מ\"עמ ללוכ אל םיפיט", text)
amount_total = extract_field(r"(\d+\.\d+)\s*:תוסנכה\s+כ.?\"?הס", text)
total_income = extract_field(r"(\d+\.\d+)\s*:תוסנכה\s+כ.?\"?הס", text)
summary = extract_field(r"([\d,]+\.\d+)\s*:\s*םייניב םוכיס", text)
internal_vendor_id = extract_field(r"(\d+)\s*:ימינפ קפס רפסמ", text)
billing_cycle = extract_field(r"(\d{2}\.\d{2}\.\d{4})\s*[:בויח רוזחמ].*?(\d{2}\.\d{2}\.\d{4})", text)


# הדפסה לבדיקה
print("קבלה (דוח על תשלומים):", document_id)
print("הכנסות חייבות במע\"מ (ללא טיפים):", taxable_income)
print("טיפים לא כולל מע\"מ:", tips)
print("סה\"כ הכנסות 1 :", amount_total)
print("סה\"כ הכנסות:", total_income)
print("סכום הניכויים:", deduction)
print("סיכום ביניים:", summary)
print("סכום סופי לתשלום:", final_amount)
print("תאריך תשלום:", date)
print("פרטי המשלם:", vendor)
print("מספר ספק פנימי:", internal_vendor_id)
print("מחזור חיוב:", billing_cycle)
print("סימוכין - מסמך מספר:", invoice_id)


import sqlite3

conn = sqlite3.connect("receipts_v2.db")
cursor = conn.cursor()

# בדיקה אם הקבלה כבר קיימת במסד לפי document_id
cursor.execute("SELECT COUNT(*) FROM receipts WHERE document_id = ?", (document_id,))
exists = cursor.fetchone()[0] > 0

if exists:
    print(f"⚠️ הולההה מותק שלי, הקבלה  {document_id} כבר קיימת במסד שלך. לא הכנסתי אותה שוב. "
          f"love ya. xo xo  .")
else:
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
        text
    ))

    conn.commit()
    print(f"✅ הקבלה עם מספר {document_id} נשמרה בהצלחה למסד.")

conn.close()

