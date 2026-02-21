import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import os
import io
from fpdf import FPDF

# --- 1. SETTINGS & PAGE CONFIG ---
st.set_page_config(page_title="Strategy Dashboard", layout="wide")
st.title("📊 Strategy Performance Dashboard")

# --- 1. PASSWORD PROTECTION ---
def check_password():
    """Returns True if the user had the correct password."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    # Show login UI
    st.title("🔒 Confidential Access")
    password = st.text_input("Enter Password", type="password")
    if st.button("Login"):
        # SET YOUR PASSWORD HERE
        if password == st.secrets["APP_PASSWORD"]:
        #if password == "Flex2026!":

            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("😕 Password incorrect")
    return False

if not check_password():
    st.stop()  # Stop the script here if not logged in

# --- 2. PDF GENERATION LOGIC ---
class StrategyPDF(FPDF):
    def header(self):
        self.set_font("Arial", 'B', 15)
        self.cell(0, 10, "Strategy Performance Factsheet", ln=True, align='C')
        self.ln(5)


def create_pdf(strategy_name, stats, nav_plot_buf, pivot_table):
    pdf = StrategyPDF() # This uses your class defined earlier
    pdf.add_page()

    # Strategy Title
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Strategy: {strategy_name}", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, f"Report Generated: {pd.Timestamp.now().strftime('%Y-%m-%d')}", ln=True)
    pdf.ln(5)

    # Statistics Table
    # UPDATED IMAGE LINE FOR FPDF2
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Growth of 100 (NAV Line)", ln=True)

    labels = ["Cumulative Return", "Annualized Return", "Annualized Volatility", "Sharpe Ratio", "Max Drawdown"]
    values = [f"{stats[0]:.2%}", f"{stats[1]:.2%}", f"{stats[2]:.2%}", f"{stats[3]:.2f}", f"{stats[4]:.2%}"]

    for label, val in zip(labels, values):
        pdf.cell(50, 8, label, border=1)
        pdf.cell(40, 8, val, border=1, ln=True)

    pdf.ln(10)

    # Insert NAV Chart
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Growth of 100 (NAV Line)", ln=True)
    # We add 'type="png"' so FPDF knows how to handle the memory buffer
    # fpdf2 handles BytesIO much better:
    pdf.image(nav_plot_buf, x=10, y=None, w=180)
    pdf.ln(5)

    # Monthly Returns Table
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Monthly Returns History", ln=True)
    pdf.set_font("Arial", '', 8)

    # Table Header (Months)
    cols = list(pivot_table.columns)
    pdf.cell(20, 7, "Year", border=1, align='C')
    for col in cols:
        pdf.cell(14, 7, col, border=1, align='C')
    pdf.ln()

    # Table Rows (Data)
    for year, row in pivot_table.iterrows():
        pdf.cell(20, 7, str(int(year)), border=1, align='C')
        for col in cols:
            val = row[col]
            text = f"{val:.2%}" if not pd.isna(val) else "-"
            pdf.cell(14, 7, text, border=1, align='C')
        pdf.ln()

    return bytes(pdf.output())


# --- 3. DATA LOADING ---
@st.cache_data
def load_data(uploaded_file=None):
    filename = "All_strategies_monthly_percentages.xlsx"
    sheet_name = "Monthly_returns"

    try:
        if uploaded_file is not None:
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
        elif os.path.exists(filename):
            df = pd.read_excel(filename, sheet_name=sheet_name)
        else:
            return None
    except Exception as e:
        st.error(f"Excel Error: {e}")
        return None

    # Clean the Data
    df = df.dropna(subset=['Date'])
    df['Date'] = pd.to_datetime(df['Date'])
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df


# Handle file loading
uploaded_xlsx = st.sidebar.file_uploader("Upload Excel file", type=["xlsx"])
df = load_data(uploaded_xlsx)

if df is None:
    st.error("❌ Data file not found. Please upload 'All_strategies_monthly_percentages.xlsx'.")
    st.stop()

# --- 4. SIDEBAR FILTERS ---
st.sidebar.header("Configuration")
strategies = [col for col in df.columns if col != 'Date']
selected_strat = st.sidebar.selectbox("Select Strategy", strategies)

min_date, max_date = df['Date'].min(), df['Date'].max()
col1, col2 = st.sidebar.columns(2)
start_dt = col1.date_input("Start", min_date, min_value=min_date, max_value=max_date)
end_dt = col2.date_input("End", max_date, min_value=min_date, max_value=max_date)

# Process Subset
mask = (df['Date'] >= pd.Timestamp(start_dt)) & (df['Date'] <= pd.Timestamp(end_dt))
subset = df.loc[mask, ['Date', selected_strat]].dropna().sort_values('Date')

if subset.empty:
    st.warning("No data found for this selection.")
    st.stop()

returns = subset[selected_strat].astype(float)


# --- 5. CALCULATIONS ---
def calc_metrics(r):
    cum_ret = (1 + r).prod() - 1
    ann_ret = (1 + cum_ret) ** (12 / len(r)) - 1 if len(r) > 0 else 0
    vol = r.std() * math.sqrt(12)
    sharpe = ann_ret / vol if vol != 0 else 0
    nav = (1 + r).cumprod()
    mdd = ((nav / nav.cummax()) - 1).min()
    return cum_ret, ann_ret, vol, sharpe, mdd


stats = calc_metrics(returns)

# --- 6. DISPLAY DASHBOARD ---

# Metric Tiles
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total Return", f"{stats[0]:.2%}")
m2.metric("Ann. Return", f"{stats[1]:.2%}")
m3.metric("Ann. Vol", f"{stats[2]:.2%}")
m4.metric("Sharpe", f"{stats[3]:.2f}")
m5.metric("Max DD", f"{stats[4]:.2%}")

# Line Chart
st.subheader(f"Growth of 100: {selected_strat}")
fig, ax = plt.subplots(figsize=(10, 4))
nav_series = (1 + returns).cumprod() * 100
ax.plot(subset['Date'], nav_series, color='#1f77b4', linewidth=2)
ax.fill_between(subset['Date'], nav_series, 100, alpha=0.1, color='#1f77b4')
ax.axhline(100, color='black', linestyle='--', alpha=0.3)
ax.grid(True, alpha=0.3)
st.pyplot(fig)

# Monthly Table
st.subheader("Monthly Returns")
subset['Year'] = subset['Date'].dt.year
subset['Month'] = subset['Date'].dt.strftime('%b')
pivot = subset.pivot(index='Year', columns='Month', values=selected_strat)
month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
pivot = pivot.reindex(columns=[m for m in month_order if m in pivot.columns])
st.dataframe(pivot.style.format("{:.2%}", na_rep="-"), use_container_width=True)
# --- 7. EXPORT PDF ---
st.sidebar.markdown("---")
if st.sidebar.button("🛠️ Prepare PDF Report"):
    # Save chart to memory
    img_buf = io.BytesIO()
    fig.savefig(img_buf, format="png", bbox_inches='tight', dpi=150)
    img_buf.seek(0)

    # Generate PDF and convert bytearray to bytes
    pdf_output = create_pdf(selected_strat, stats, img_buf, pivot)
    pdf_bytes = bytes(pdf_output) # <--- THIS FIXES THE ERROR

    st.sidebar.download_button(
        label="📥 Download PDF",
        data=pdf_bytes,
        file_name=f"{selected_strat}_Report.pdf",
        mime="application/pdf"
    )

st.success("Access Granted")