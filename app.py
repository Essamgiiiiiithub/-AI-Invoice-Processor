import streamlit as st
import os
import sqlite3
import subprocess
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from ocr_engine import extract_text
from ai_extractor import extract_document_data
from data_handler import init_database, save_invoice, get_all_invoices, get_invoices_df, delete_invoice

import tempfile
DB_PATH  = os.path.join(tempfile.gettempdir(), "documents.db")
EXCEL_PATH = os.path.join(os.getcwd(), "documents.xlsx")

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Document Processor",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

*, *::before, *::after { font-family: 'Plus Jakarta Sans', sans-serif !important; box-sizing: border-box; }

/* ── Hide Streamlit chrome ── */
footer, #MainMenu, header { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; }

/* ── Hero ── */
.hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f2942 100%);
    padding: 2rem 2.5rem;
    border-radius: 20px;
    color: white;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(99,179,237,0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.hero::after {
    content: '';
    position: absolute;
    bottom: -30px; left: 30%;
    width: 300px; height: 150px;
    background: radial-gradient(ellipse, rgba(139,92,246,0.1) 0%, transparent 70%);
}
.hero-inner { position: relative; z-index: 1; }
.hero h1 { font-size: 1.9rem; font-weight: 800; margin: 0; letter-spacing: -0.5px; }
.hero p  { font-size: 0.92rem; opacity: 0.7; margin: 0.4rem 0 0; }
.hero-badge {
    display: inline-block;
    background: rgba(99,179,237,0.2);
    border: 1px solid rgba(99,179,237,0.35);
    color: #63b3ed;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 0.75rem;
    letter-spacing: 0.5px;
}

/* ── KPI Cards ── */
.kpi-card {
    background: white;
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    border: 1px solid #e8edf5;
    box-shadow: 0 2px 8px rgba(15,23,42,0.06);
    position: relative;
    overflow: hidden;
    transition: transform .2s, box-shadow .2s;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(15,23,42,0.1); }
.kpi-card::after {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 4px; height: 100%;
    border-radius: 0 16px 16px 0;
}
.kpi-blue::after   { background: #3b82f6; }
.kpi-purple::after { background: #8b5cf6; }
.kpi-green::after  { background: #10b981; }
.kpi-orange::after { background: #f59e0b; }
.kpi-icon  { font-size: 1.6rem; margin-bottom: 0.5rem; }
.kpi-num   { font-size: 1.9rem; font-weight: 800; color: #0f172a; line-height: 1; }
.kpi-label { font-size: 0.78rem; color: #64748b; font-weight: 500; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
.kpi-sub   { font-size: 0.78rem; color: #94a3b8; margin-top: 6px; }

/* ── Invoice Cards ── */
.inv-card {
    background: white;
    border-radius: 14px;
    padding: 1rem 1.2rem;
    border: 1px solid #e8edf5;
    margin-bottom: 10px;
    box-shadow: 0 1px 4px rgba(15,23,42,0.05);
    transition: box-shadow .2s;
}
.inv-card:hover { box-shadow: 0 4px 12px rgba(15,23,42,0.09); }
.inv-name  { font-size: 0.95rem; font-weight: 700; color: #0f172a; }
.inv-row   { font-size: 0.82rem; color: #475569; margin: 3px 0; }
.inv-amount { font-size: 1.1rem; font-weight: 700; color: #3b82f6; }
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.73rem;
    font-weight: 600;
}
.badge-blue   { background: #dbeafe; color: #1d4ed8; }
.badge-green  { background: #dcfce7; color: #166534; }
.badge-purple { background: #ede9fe; color: #6d28d9; }

/* ── Upload zone ── */
[data-testid="stFileUploader"] {
    background: #f8faff;
    border: 2px dashed #93c5fd;
    border-radius: 14px;
    padding: 0.5rem;
    transition: border-color .2s;
    color: #0f172a !important;
}
[data-testid="stFileUploader"]:hover { border-color: #3b82f6; }
[data-testid="stFileUploader"] *,
section[data-testid="stFileUploadDropzone"] {
    color: #0f172a !important;
}
section[data-testid="stFileUploadDropzone"] {
    background: #eff6ff !important;
    padding: 1.5rem !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #f1f5f9;
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
    border: none !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 8px 20px !important;
    color: #64748b !important;
    border: none !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    background: white !important;
    color: #0f172a !important;
    box-shadow: 0 1px 6px rgba(15,23,42,0.1) !important;
}

/* ── Section titles ── */
.section-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #e2e8f0;
    margin-left: 8px;
}

/* ── Chart container ── */
.chart-box {
    background: white;
    border-radius: 16px;
    border: 1px solid #e8edf5;
    box-shadow: 0 2px 8px rgba(15,23,42,0.05);
    padding: 1rem;
    margin-bottom: 1rem;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: #94a3b8;
}
.empty-state .emoji { font-size: 3rem; margin-bottom: 1rem; }
.empty-state p { font-size: 0.9rem; }

/* ── Expander (Danger Zone) ── */
.stExpander {
    border: 3px solid #ef4444 !important;
    border-radius: 12px !important;
    background: white !important;
}
.stExpander > button {
    background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%) !important;
    color: #991b1b !important;
    font-weight: 800 !important;
    font-size: 1.05rem !important;
    padding: 1.2rem !important;
    border: none !important;
}
.stExpander > button:hover {
    background: linear-gradient(135deg, #fecaca 0%, #fca5a5 100%) !important;
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3) !important;
}
section[data-testid="stExpander"] {
    background: #fffbfb !important;
    border-radius: 12px !important;
}
section[data-testid="stExpander"] > div {
    padding: 1.5rem !important;
    background: #fffbfb !important;
}
section[data-testid="stExpander"] p,
section[data-testid="stExpander"] span,
section[data-testid="stExpander"] div {
    color: #0f172a !important;
    font-weight: 500 !important;
}


/* ── Warning boxes ── */
.stAlert {
    color: #0f172a !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Init ─────────────────────────────────────────────────────────────────────
init_database()
os.makedirs("outputs", exist_ok=True)

# ── Helpers ──────────────────────────────────────────────────────────────────
def update_excel(data, file_name):
    new_row = {
        "Document Type":   data.get("document_type") or "—",
        "Title":           data.get("title") or "—",
        "Description":     data.get("description") or "—",
        "Supplier Name":   data.get("supplier_name") or "—",
        "Document Number":  data.get("invoice_number") or "—",
        "Date":            data.get("date") or "—",
        "Total Amount":    data.get("total_amount") or "—",
        "Numeric Total":   data.get("numeric_total") or "",
        "Tax Amount":      data.get("tax_amount") or "—",
        "Currency":        data.get("currency") or "—",
        "Items":           ", ".join(data.get("items") or []) or "—",
        "Payment Method":  data.get("payment_method") or "—",
        "Notes":           data.get("notes") or "",
        "File Name":       file_name,
        "Added At":        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    try:
        if os.path.exists(EXCEL_PATH):
            df = pd.read_excel(EXCEL_PATH)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        else:
            df = pd.DataFrame([new_row])

        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Documents")
            ws = writer.sheets["Documents"]
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            hf = PatternFill("solid", fgColor="0F2942")
            hfont = Font(bold=True, color="FFFFFF", size=11)
            border = Border(left=Side(style="thin"), right=Side(style="thin"),
                            top=Side(style="thin"), bottom=Side(style="thin"))
            for cell in ws[1]:
                cell.fill = hf; cell.font = hfont
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = border
            for row in ws.iter_rows(min_row=2):
                for cell in row:
                    cell.border = border
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                    if cell.row % 2 == 0:
                        cell.fill = PatternFill("solid", fgColor="F0F6FF")
            ws.freeze_panes = "A2"
            ws.row_dimensions[1].height = 30
        return True
    except Exception as e:
        st.error(f"Excel error: {e}")
        return False

def make_chart(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_family="Plus Jakarta Sans",
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#f1f5f9", zeroline=False)
    return fig

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-inner">
    <div class="hero-badge">POWERED BY GROQ · LLAMA 3.3 70B</div>
    <h1>AI Document Processor</h1>
    <p>Scan · Extract · Analyze · Export — all in seconds</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPI Row ───────────────────────────────────────────────────────────────────
df_all = get_invoices_df()
total_invoices = len(df_all)
total_suppliers = df_all["supplier_name"].nunique() if not df_all.empty else 0
total_amount = df_all["numeric_total"].sum() if not df_all.empty and "numeric_total" in df_all.columns else 0
avg_amount = df_all["numeric_total"].mean() if not df_all.empty and "numeric_total" in df_all.columns and total_invoices > 0 else 0

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f"""<div class="kpi-card kpi-blue">
        <div class="kpi-icon">🧾</div>
        <div class="kpi-num">{total_invoices}</div>
        <div class="kpi-label">Total Documents</div>
    </div>""", unsafe_allow_html=True)
with k2:
    st.markdown(f"""<div class="kpi-card kpi-purple">
        <div class="kpi-num">{total_suppliers}</div>
        <div class="kpi-label">Suppliers</div>
    </div>""", unsafe_allow_html=True)
with k3:
    fmt = f"{total_amount:,.0f}" if total_amount else "—"
    st.markdown(f"""<div class="kpi-card kpi-green">
        <div class="kpi-num">{fmt}</div>
        <div class="kpi-label">Total Spent</div>
    </div>""", unsafe_allow_html=True)
with k4:
    fmt2 = f"{avg_amount:,.0f}" if avg_amount else "—"
    st.markdown(f"""<div class="kpi-card kpi-orange">
        <div class="kpi-num">{fmt2}</div>
        <div class="kpi-label">Avg per Document</div>
    </div>""", unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["Upload Document", "Dashboard", "History"])

# ═══════════════════════════════════════════════════════════
#  TAB 1 — UPLOAD
# ═══════════════════════════════════════════════════════════
with tab1:
    col_up, col_res = st.columns([1, 1], gap="large")

    with col_up:
        st.markdown('<div class="section-title">Upload New Document</div>', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Drag & drop document image or PDF or click to browse",
            type=["jpg", "jpeg", "png", "bmp", "pdf"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        if uploaded_files:
            def is_image(filename):
                return os.path.splitext(filename)[1].lower() in [".jpg", ".jpeg", ".png", ".bmp"]

            if len(uploaded_files) == 1:
                if is_image(uploaded_files[0].name):
                    st.image(uploaded_files[0], use_container_width=True, caption=uploaded_files[0].name)
                else:
                    st.markdown(f"**Uploaded document:** {uploaded_files[0].name}")
            else:
                st.markdown("**Selected documents:**")
                for file_item in uploaded_files:
                    if is_image(file_item.name):
                        st.write(f"- {file_item.name} (image)")
                    else:
                        st.write(f"- {file_item.name} (document)")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Analyze Documents", type="primary", use_container_width=True):
                processed = 0
                last_data = None
                for uploaded_file in uploaded_files:
                    with st.spinner(f"⏳ Reading text from {uploaded_file.name}..."):
                        file_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        text, error = extract_text(file_path)

                    if error:
                        st.error(f"{uploaded_file.name}: {error}")
                        continue
                    if not text:
                        st.error(f"{uploaded_file.name}: No text found. Try a clearer photo.")
                        continue

                    with st.spinner(f"🤖 AI extracting document data for {uploaded_file.name}..."):
                        data = extract_document_data(text)
                        save_invoice(data, uploaded_file.name)
                        excel_ok = update_excel(data, uploaded_file.name)

                    last_data = data
                    processed += 1
                    if not excel_ok:
                        st.warning(f"{uploaded_file.name}: Saved to database but Excel update failed.")

                if processed:
                    st.success(f"{processed} document(s) analyzed and saved!")
                    st.session_state["last_result"] = last_data
                else:
                    st.warning("No documents were processed.")
                st.rerun()

    with col_res:
        st.markdown('<div class="section-title">Extracted Information</div>', unsafe_allow_html=True)
        result = st.session_state.get("last_result")
        if result:
            # Amount highlight
            if result.get("total_amount"):
                st.metric("Total Amount", result.get("total_amount") or "—")

            r1, r2 = st.columns(2)
            with r1:
                st.metric("Supplier",    result.get("supplier_name") or "—")
                st.metric("Date",        result.get("date") or "—")
                st.metric("🧾 Tax",         result.get("tax_amount") or "—")
            with r2:
                st.metric("Document No.", result.get("invoice_number") or "—")
                st.metric("Payment",     result.get("payment_method") or "—")
                items = result.get("items") or []
                st.metric("Items",       len(items))

            if result.get("document_type"):
                st.metric("Document Type", result.get("document_type"))
            if result.get("title"):
                st.metric("📋 Title", result.get("title"))
            if result.get("description"):
                st.metric("📝 Description", result.get("description"))

            if items:
                st.markdown("**Items / Services:**")
                for item in items:
                    st.markdown(f"<span class='badge badge-blue'>• {item}</span> ", unsafe_allow_html=True)

            if result.get("notes"):
                st.info(f" {result['notes']}")
        else:
            st.markdown('<div class="empty-state"><p>Upload and analyze a document to see extracted information here</p></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
#  TAB 2 — DASHBOARD
# ═══════════════════════════════════════════════════════════
with tab2:
    if df_all.empty:
        st.markdown('<div class="empty-state" style="padding:4rem"><p>No data yet - upload some documents first<br>and the dashboard will come alive!</p></div>', unsafe_allow_html=True)
    else:
        COLORS = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444",
                  "#06b6d4", "#ec4899", "#84cc16", "#f97316", "#6366f1"]

        df_chart = df_all.copy()

        # ── Row 1: Supplier bar + Monthly line ──
        ch1, ch2 = st.columns(2, gap="medium")

        with ch1:
            st.markdown('<div class="section-title">🏢 Top Suppliers by Amount</div>', unsafe_allow_html=True)
            sup_df = (df_chart.dropna(subset=["numeric_total"])
                              .groupby("supplier_name", as_index=False)["numeric_total"].sum()
                              .sort_values("numeric_total", ascending=False)
                              .head(8))
            if not sup_df.empty:
                fig = px.bar(sup_df, x="numeric_total", y="supplier_name",
                             orientation="h", color="supplier_name",
                             color_discrete_sequence=COLORS,
                             labels={"numeric_total": "Total Amount", "supplier_name": ""})
                fig.update_traces(marker_line_width=0)
                fig.update_layout(showlegend=False, height=320)
                st.plotly_chart(make_chart(fig), use_container_width=True)
            else:
                st.info("Not enough numeric data yet.")

        with ch2:
            st.markdown('<div class="section-title">📅 Monthly Spending Trend</div>', unsafe_allow_html=True)
            df_chart["created_at"] = pd.to_datetime(df_chart["created_at"], errors="coerce")
            df_chart["month"] = df_chart["created_at"].dt.to_period("M").astype(str)
            monthly = (df_chart.dropna(subset=["numeric_total"])
                               .groupby("month", as_index=False)["numeric_total"].sum()
                               .sort_values("month"))
            if not monthly.empty:
                fig2 = px.area(monthly, x="month", y="numeric_total",
                               color_discrete_sequence=["#3b82f6"],
                               labels={"numeric_total": "Amount", "month": ""})
                fig2.update_traces(fill="tozeroy", line_color="#3b82f6",
                                   fillcolor="rgba(59,130,246,0.15)")
                fig2.update_layout(height=320)
                st.plotly_chart(make_chart(fig2), use_container_width=True)
            else:
                st.info("Not enough data for trend.")

        # ── Row 2: Pie + Invoice count bar ──
        ch3, ch4 = st.columns(2, gap="medium")

        with ch3:
            st.markdown('<div class="section-title">🥧 Spending Distribution</div>', unsafe_allow_html=True)
            pie_df = (df_chart.dropna(subset=["numeric_total"])
                              .groupby("supplier_name", as_index=False)["numeric_total"].sum()
                              .sort_values("numeric_total", ascending=False))
            if len(pie_df) > 5:
                top5   = pie_df.head(5)
                others = pd.DataFrame([{"supplier_name": "Others",
                                        "numeric_total": pie_df.iloc[5:]["numeric_total"].sum()}])
                pie_df = pd.concat([top5, others])
            if not pie_df.empty:
                fig3 = px.pie(pie_df, names="supplier_name", values="numeric_total",
                              color_discrete_sequence=COLORS, hole=0.45)
                fig3.update_traces(textposition="outside", textinfo="percent+label")
                fig3.update_layout(height=320, showlegend=False)
                st.plotly_chart(make_chart(fig3), use_container_width=True)

        with ch4:
            st.markdown('<div class="section-title">🔢 Documents per Supplier</div>', unsafe_allow_html=True)
            cnt_df = (df_chart.groupby("supplier_name", as_index=False)
                              .size().rename(columns={"size": "count"})
                              .sort_values("count", ascending=False).head(8))
            if not cnt_df.empty:
                fig4 = px.bar(cnt_df, x="supplier_name", y="count",
                              color="supplier_name", color_discrete_sequence=COLORS,
                              labels={"count": "# Documents", "supplier_name": ""})
                fig4.update_traces(marker_line_width=0)
                fig4.update_layout(showlegend=False, height=320)
                fig4.update_xaxes(tickangle=-25)
                st.plotly_chart(make_chart(fig4), use_container_width=True)

        # ── Document type distribution ──
        st.markdown('<div class="section-title">🗂️ Document Type Distribution</div>', unsafe_allow_html=True)
        if "document_type" in df_chart.columns and not df_chart["document_type"].dropna().empty:
            type_df = (df_chart["document_type"].fillna("Unknown")
                                  .value_counts()
                                  .reset_index())
            type_df.columns = ["document_type", "count"]
            fig_type = px.pie(type_df, names="document_type", values="count",
                              color_discrete_sequence=COLORS, hole=0.45)
            fig_type.update_traces(textposition="outside", textinfo="percent+label")
            fig_type.update_layout(height=320, showlegend=False)
            st.plotly_chart(make_chart(fig_type), use_container_width=True)
        else:
            st.info("Upload documents with a detected type to see this chart.")

        # ── Tax analysis ──
        st.markdown('<div class="section-title">🧾 Tax vs Amount Analysis</div>', unsafe_allow_html=True)
        tax_df = df_chart.dropna(subset=["numeric_total", "numeric_tax"])
        if not tax_df.empty:
            fig5 = go.Figure()
            fig5.add_trace(go.Bar(name="Total Amount", x=tax_df["supplier_name"],
                                  y=tax_df["numeric_total"], marker_color="#3b82f6"))
            fig5.add_trace(go.Bar(name="Tax", x=tax_df["supplier_name"],
                                  y=tax_df["numeric_tax"], marker_color="#f59e0b"))
            fig5.update_layout(barmode="group", height=300,
                                legend=dict(orientation="h", y=1.1))
            st.plotly_chart(make_chart(fig5), use_container_width=True)
        else:
            st.info("Upload more documents with tax data to see this chart.")

# ═══════════════════════════════════════════════════════════
#  TAB 3 — HISTORY
# ═══════════════════════════════════════════════════════════
with tab3:
    col_list, col_actions = st.columns([2, 1], gap="large")

    with col_list:
        st.markdown('<div class="section-title">📋 All Documents</div>', unsafe_allow_html=True)
        invoices = get_all_invoices()
        if invoices:
            for inv in invoices:
                amount_html = f'<span class="inv-amount">{inv.get("total_amount") or "—"}</span>' if inv.get("total_amount") else '<span style="color:#94a3b8">No amount</span>'
                st.write("test")
        else:
            st.markdown('<div class="empty-state"><p>No documents yet<br>Upload your first document!</p></div>', unsafe_allow_html=True)

    with col_actions:
        st.markdown('<div class="section-title">Actions</div>', unsafe_allow_html=True)

        # Export Excel
        if st.button("Export to Excel", use_container_width=True, type="primary"):
            if os.path.exists(EXCEL_PATH):
                subprocess.Popen(f'start excel "{EXCEL_PATH}"', shell=True)
                st.success("✅ Opening Excel...")
            else:
                st.warning("⚠️ No Excel file yet — analyze a document first!")

        # Download Excel
        if os.path.exists(EXCEL_PATH):
            with open(EXCEL_PATH, "rb") as f:
                st.download_button(
                    "⬇️ Download Excel",
                    data=f,
                    file_name="documents.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

        st.markdown("<br>", unsafe_allow_html=True)

        # Stats summary
        if not df_all.empty:
            st.markdown('<div style="background:#f8faff;border-radius:12px;padding:1rem;border:1px solid #e0e7ff;">', unsafe_allow_html=True)
            st.markdown("**Quick Stats**")
            if "numeric_total" in df_all.columns:
                valid = df_all["numeric_total"].dropna()
                if not valid.empty:
                    st.markdown(f"• Max: **{valid.max():,.0f}**")
                    st.markdown(f"• Min: **{valid.min():,.0f}**")
                    st.markdown(f"• Avg: **{valid.mean():,.0f}**")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Clear all
        with st.expander("DANGER ZONE - Permanently Delete All Data", expanded=False):
            st.markdown("""
            <div style="background:#fff5f5;border-left:4px solid #ef4444;padding:1rem;border-radius:8px;margin-bottom:1rem;">
            <p style="margin:0;color:#991b1b;font-weight:700;font-size:0.95rem;">
            This will delete ALL documents permanently!
            </p>
            <p style="margin:0.5rem 0 0;color:#7f1d1d;font-size:0.85rem;">
            This action cannot be undone. Make sure you have backed up your data.
            </p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🗑️ Clear All Data", use_container_width=True, type="secondary"):
                conn = sqlite3.connect(DB_PATH)
                conn.execute("DELETE FROM invoices")
                conn.commit()
                conn.close()
                if os.path.exists(EXCEL_PATH):
                    try:
                        os.remove(EXCEL_PATH)
                    except PermissionError:
                        st.error("Close Excel first, then try again!")
                        st.stop()
                st.session_state.pop("last_result", None)
                st.success("All data cleared!")
                st.rerun()
