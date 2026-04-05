import sqlite3
import pandas as pd
import json
import os
from datetime import datetime

import tempfile, os
DB_PATH = os.path.join(tempfile.gettempdir(), "invoices.db")

def init_database():
    """إنشاء قاعدة البيانات"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name TEXT,
            invoice_number TEXT,
            date TEXT,
            total_amount TEXT,
            tax_amount TEXT,
            items TEXT,
            file_name TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Database ready!")

def save_invoice(data, file_name=""):
    """حفظ الفاتورة في قاعدة البيانات"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO invoices 
        (supplier_name, invoice_number, date, total_amount, tax_amount, items, file_name, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get("supplier_name"),
        data.get("invoice_number"),
        data.get("date"),
        data.get("total_amount"),
        data.get("tax_amount"),
        json.dumps(data.get("items", []), ensure_ascii=False),
        file_name,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()
    print("✅ Invoice saved to database!")

def export_to_excel():
    """تصدير كل الفواتير لـ Excel"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM invoices", conn)
    conn.close()

    output_path = f"outputs/invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(output_path, index=False)
    print(f"✅ Exported to: {output_path}")
    return output_path

def get_all_invoices():
    """جلب كل الفواتير من قاعدة البيانات"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM invoices ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


# ── تجربة الكود ──
if __name__ == "__main__":
    print("💾 Data Handler Test")
    print("=" * 40)

    # إنشاء قاعدة البيانات
    init_database()

    # بيانات تجريبية
    test_data = {
        "supplier_name": "Array Training Center",
        "invoice_number": "INV-2024-001",
        "date": "15/7/2024",
        "total_amount": "5000 EGP",
        "tax_amount": "750 EGP",
        "items": ["AI Diploma Course"]
    }

    # حفظ الفاتورة
    save_invoice(test_data, "test_invoice.jpg")

    # تصدير لـ Excel
    export_to_excel()

    print("\n🎉 All done!")