import sqlite3
import pandas as pd
import json
import os
import re
from datetime import datetime

import tempfile
DB_PATH = os.path.join(tempfile.gettempdir(), "documents.db")

def parse_numeric_value(value):
    """تحليل القيمة الرقمية من النص"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    text = text.replace(",", "")
    match = re.search(r"[-+]?[0-9]*\.?[0-9]+", text)
    return float(match.group(0)) if match else None

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
            numeric_total REAL,
            tax_amount TEXT,
            numeric_tax REAL,
            currency TEXT,
            payment_method TEXT,
            notes TEXT,
            items TEXT,
            file_name TEXT,
            created_at TEXT,
            document_type TEXT,
            title TEXT,
            description TEXT
        )
    ''')

    cursor.execute("PRAGMA table_info(invoices)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    extra_columns = [
        ("numeric_total", "REAL"),
        ("numeric_tax", "REAL"),
        ("currency", "TEXT"),
        ("payment_method", "TEXT"),
        ("notes", "TEXT"),
        ("document_type", "TEXT"),
        ("title", "TEXT"),
        ("description", "TEXT"),
    ]
    for col_name, col_type in extra_columns:
        if col_name not in existing_columns:
            cursor.execute(f"ALTER TABLE invoices ADD COLUMN {col_name} {col_type}")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_supplier ON invoices(supplier_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON invoices(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_type ON invoices(document_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoice_number ON invoices(invoice_number)")

    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")

    conn.commit()
    conn.close()
    print("تم إعداد قاعدة البيانات")

def save_invoice(data, file_name=""):
    """حفظ الفاتورة في قاعدة البيانات"""
    numeric_total = parse_numeric_value(data.get("numeric_total") or data.get("total_amount"))
    numeric_tax = parse_numeric_value(data.get("numeric_tax") or data.get("tax_amount"))

    conn = sqlite3.connect(DB_PATH)
    conn.isolation_level = None
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO invoices
            (supplier_name, invoice_number, date, total_amount, numeric_total,
             tax_amount, numeric_tax, currency, payment_method, notes, items, file_name, created_at,
             document_type, title, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get("supplier_name"),
            data.get("invoice_number"),
            data.get("date"),
            data.get("total_amount"),
            numeric_total,
            data.get("tax_amount"),
            numeric_tax,
            data.get("currency"),
            data.get("payment_method"),
            data.get("notes"),
            json.dumps(data.get("items", []), ensure_ascii=False),
            file_name,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data.get("document_type"),
            data.get("title"),
            data.get("description")
        ))
        print("تم حفظ الفاتورة")
    except Exception as e:
        print(f"خطأ في حفظ الفاتورة: {e}")
    finally:
        conn.close()

def save_invoices_batch(data_list):
    """حفظ عدة فواتير دفعة واحدة"""
    if not data_list:
        return

    conn = sqlite3.connect(DB_PATH)
    conn.isolation_level = None
    cursor = conn.cursor()

    try:
        for data in data_list:
            numeric_total = parse_numeric_value(data.get("numeric_total") or data.get("total_amount"))
            numeric_tax = parse_numeric_value(data.get("numeric_tax") or data.get("tax_amount"))

            cursor.execute('''
                INSERT INTO invoices
                (supplier_name, invoice_number, date, total_amount, numeric_total,
                 tax_amount, numeric_tax, currency, payment_method, notes, items, file_name, created_at,
                 document_type, title, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get("supplier_name"),
                data.get("invoice_number"),
                data.get("date"),
                data.get("total_amount"),
                numeric_total,
                data.get("tax_amount"),
                numeric_tax,
                data.get("currency"),
                data.get("payment_method"),
                data.get("notes"),
                json.dumps(data.get("items", []), ensure_ascii=False),
                data.get("file_name", ""),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                data.get("document_type"),
                data.get("title"),
                data.get("description")
            ))
        print(f"تم حفظ {len(data_list)} فاتورة")
    except Exception as e:
        print(f"خطأ في حفظ الدفعة: {e}")
    finally:
        conn.close()

def export_to_excel():
    """تصدير الفواتير إلى Excel"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM invoices", conn)
    conn.close()

    output_path = f"outputs/invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(output_path, index=False)
    print(f"تم التصدير إلى: {output_path}")
    return output_path

def get_all_invoices():
    """جلب جميع الفواتير"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM invoices ORDER BY created_at DESC LIMIT 500")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_invoices_df():
    """إرجاع الفواتير كـ DataFrame"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM invoices ORDER BY created_at DESC LIMIT 500", conn)
    conn.close()

    if df.empty:
        return df

    if "items" in df.columns:
        df["items"] = df["items"].apply(
            lambda x: json.loads(x) if isinstance(x, str) and x.strip() else []
        )

    if "numeric_total" not in df.columns or df["numeric_total"].isnull().all():
        if "total_amount" in df.columns:
            df["numeric_total"] = df["total_amount"].apply(parse_numeric_value)

    if "numeric_tax" not in df.columns or df["numeric_tax"].isnull().all():
        if "tax_amount" in df.columns:
            df["numeric_tax"] = df["tax_amount"].apply(parse_numeric_value)

    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    return df

def delete_invoice(invoice_id):
    """حذف فاتورة"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
    conn.commit()
    conn.close()
