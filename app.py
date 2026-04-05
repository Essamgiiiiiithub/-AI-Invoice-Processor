import streamlit as st
import os
import sqlite3
import subprocess
import pandas as pd
from datetime import datetime
from ocr_engine import extract_text
from ai_extractor import extract_invoice_data
from data_handler import init_database, save_invoice, get_all_invoices

DB_PATH = "database/invoices.db"
EXCEL_PATH = os.path.abspath("outputs/invoices_database.xlsx")

st.set_page_config(
    page_title="AI Invoice Processor",
    page_icon="🧾",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    * { font-family: 'Inter', sans-serif !important; }
    .hero {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .hero h1 { font-size: 2.2rem; font-weight: 700; margin: 0; }
    .hero p  { font-size: 1rem; opacity: 0.85; margin: 0.5rem 0 0; }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        text-align: center;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .metric-card .num { font-size: 2rem; font-weight: 700; color: #667eea; }
    .metric-card .lbl { font-size: 0.85rem; color: #64748b; margin-top: 4px; }
    .invoice-card {
        background: white;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .invoice-title { font-size: 1rem; font-weight: 700; color: #1e293b; margin-bottom: 6px; }
    .invoice-row { font-size: 0.85rem; color: #475569; margin: 3px 0; }
    .badge {
        display: inline-block;
        background: #ede9fe;
        color: #6d28d9;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    [data-testid="stFileUploader"] {
        background: white;
        border: 2px dashed #667eea;
        border-radius: 12px;
        padding: 1rem;
    }
    section[data-testid="stFileUploadDropzone"] {
        background: #f8f7ff !important;
        border-radius: 10px;
        padding: 1.5rem !important;
    }
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

init_database()
os.makedirs("outputs", exist_ok=True)

# ── Save to Excel ──
def update_excel(data, file_name):
    new_row = {
        "Supplier Name":   data.get("supplier_name") or "—",
        "Invoice Number":  data.get("invoice_number") or "—",
        "Date":            data.get("date") or "—",
        "Total Amount":    data.get("total_amount") or "—",
        "Tax Amount":      data.get("tax_amount") or "—",
        "Items":           ", ".join(data.get("items") or []) or "—",
        "File Name":       file_name,
        "Added At":        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    try:
        os.makedirs("outputs", exist_ok=True)
        if os.path.exists(EXCEL_PATH):
            df = pd.read_excel(EXCEL_PATH)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        else:
            df = pd.DataFrame([new_row])

        # حفظ مع تنسيق احترافي
        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Invoices")
            ws = writer.sheets["Invoices"]

            # عرض الأعمدة تلقائي
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

            # تنسيق الهيدر
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            header_fill = PatternFill("solid", fgColor="667EEA")
            header_font = Font(bold=True, color="FFFFFF", size=11)
            border = Border(
                left=Side(style="thin"),
                right=Side(style="thin"),
                top=Side(style="thin"),
                bottom=Side(style="thin")
            )

            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                cell.border = border

            # تنسيق الصفوف
            for row in ws.iter_rows(min_row=2):
                for i, cell in enumerate(row):
                    cell.border = border
                    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                    # تلوين صفوف متناوبة
                    if cell.row % 2 == 0:
                        cell.fill = PatternFill("solid", fgColor="F0F4FF")

            # تثبيت الهيدر
            ws.freeze_panes = "A2"
            ws.row_dimensions[1].height = 30

        return True
    except Exception as e:
        st.error(f"Excel error: {e}")
        return False
# ── Hero ──
st.markdown("""
<div class="hero">
    <h1>🧾 AI Invoice Processor</h1>
    <p>Instant AI analysis — Auto save — Excel export</p>
</div>
""", unsafe_allow_html=True)

# ── Metrics ──
invoices = get_all_invoices()
total = len(invoices)
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT COUNT(DISTINCT supplier_name) FROM invoices WHERE supplier_name IS NOT NULL AND supplier_name != 'None'")
suppliers = cur.fetchone()[0]
conn.close()

m1, m2, m3 = st.columns(3)
with m1:
    st.markdown(f"""<div class="metric-card">
        <div class="num">{total}</div>
        <div class="lbl">Total Invoices</div>
    </div>""", unsafe_allow_html=True)
with m2:
    st.markdown(f"""<div class="metric-card">
        <div class="num">{suppliers}</div>
        <div class="lbl">Total Suppliers</div>
    </div>""", unsafe_allow_html=True)
with m3:
    st.markdown(f"""<div class="metric-card">
        <div class="num" style="color:#10b981">✓</div>
        <div class="lbl">System Online</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Main columns ──
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📤 Upload New Invoice")
    uploaded_file = st.file_uploader(
        "Drag & drop invoice here or click to browse",
        type=["jpg", "jpeg", "png", "bmp"]
    )

    if uploaded_file:
        st.image(uploaded_file, use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🔍 Analyze Invoice", type="primary", use_container_width=True):
            with st.spinner("⏳ Reading text from image..."):
                file_path = f"uploads/{uploaded_file.name}"
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                text, error = extract_text(file_path)

            if error:
                st.error(f"❌ {error}")
            elif not text:
                st.error("❌ No text found in image. Try a clearer photo.")
            else:
                with st.spinner("🤖 AI is extracting invoice data..."):
                    data = extract_invoice_data(text)
                    save_invoice(data, uploaded_file.name)
                    excel_ok = update_excel(data, uploaded_file.name)

                if excel_ok:
                    st.success("✅ Invoice analyzed and saved to Database & Excel!")
                else:
                    st.warning("⚠️ Saved to database but Excel failed.")

                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Supplier",       data.get("supplier_name") or "—")
                    st.metric("Date",            data.get("date") or "—")
                    st.metric("Tax",             data.get("tax_amount") or "—")
                with c2:
                    st.metric("Invoice No.",     data.get("invoice_number") or "—")
                    st.metric("Total Amount",    data.get("total_amount") or "—")
                    items = data.get("items") or []
                    st.metric("Items Count",     len(items))

                if items:
                    st.markdown("**Items / Services:**")
                    for item in items:
                        st.markdown(f"- {item}")
                st.rerun()

with col2:
    st.markdown("### 📋 Saved Invoices")
    if invoices:
        for inv in invoices:
            st.markdown(f"""
            <div class="invoice-card">
                <div class="invoice-title">🏢 {inv[1] or 'Unknown'}</div>
                <div class="invoice-row">🔢 Invoice No: <b>{inv[2] or '—'}</b></div>
                <div class="invoice-row">📅 Date: <b>{inv[3] or '—'}</b></div>
                <div class="invoice-row">💰 Amount: <b>{inv[4] or '—'}</b></div>
                <div class="invoice-row">🧾 Tax: <b>{inv[5] or '—'}</b></div>
                <div style="margin-top:8px">
                    <span class="badge">📎 {inv[7] or 'unknown'}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📭 No invoices yet — upload your first invoice!")

# ── Footer ──
st.markdown("<br>", unsafe_allow_html=True)
st.divider()
fc1, fc2, fc3 = st.columns([1, 1, 2])

with fc1:
    if st.button("📊 Open Excel File", use_container_width=True):
        if os.path.exists(EXCEL_PATH):
            subprocess.Popen(
                f'start excel "{EXCEL_PATH}"',
                shell=True
            )
            st.success("✅ Opening Excel...")
        else:
            st.warning("⚠️ No Excel file yet — analyze an invoice first!")

with fc2:
    if st.button("🗑️ Clear All Data", use_container_width=True):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM invoices")
        conn.commit()
        conn.close()
        if os.path.exists(EXCEL_PATH):
            try:
                os.remove(EXCEL_PATH)
            except PermissionError:
                st.error("⚠️ Please close the Excel file first, then click again!")
                st.stop()
        st.success("✅ All data cleared!")
        st.rerun()