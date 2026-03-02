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

# --- 2. PERMISSIONS & ROLES ---
STRATEGY_GROUPS = {
    "admin": "all",
    "manager": [
        "Wealth strategy", "Crypto LS", "BTC defencive", "ETh defencive", "BTC", "ETH",
        "Commodities", "Equities", "Equities Euro Hedged", "Hedge Funds",
        "Hedge Funds Euro Hedged", "Fixed Income", "Indices", "Stocks", "AI Equities",
        "SMA Crypto", "ARC Euro Cautious PCI", "Equities_CDNE", "Equities_CDNE_Euro_Hedged"
    ],
    "client": ["Wealth strategy", "Equities"]
}


# --- 3. PASSWORD PROTECTION ---
def check_password():
    if "user_role" not in st.session_state:
        st.session_state["user_role"] = None

    if st.session_state["user_role"] is not None:
        return True

    st.title("🔒 Confidential Access")
    password = st.text_input("Enter Access Code", type="password")

    if st.button("Login"):
        if password == st.secrets["PWD_ADMIN"]:
            st.session_state["user_role"] = "admin"
            st.rerun()
        elif password == st.secrets["PWD_MANAGER"]:
            st.session_state["user_role"] = "manager"
            st.rerun()
        elif password == st.secrets["PWD_CLIENT"]:
            st.session_state["user_role"] = "client"
            st.rerun()
        else:
            st.error("😕 Access code incorrect")
    return False


if not check_password():
    st.stop()


# --- 4. PDF GENERATION LOGIC ---
class StrategyPDF(FPDF):
    def header(self):
        self.set_font("Arial", 'B', 15)
        self.cell(0, 10, "Strategy Performance Factsheet", ln=True, align='C')
        self.ln(5)


def create_pdf(strategy_name, stats, nav_plot_buf, pivot_table):
    pdf = StrategyPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Strategy: {strategy_name}", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, f"Report Generated: {pd.Timestamp.now().strftime('%Y-%m-%d')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Performance Summary", ln=True)
    labels = ["Cumulative Return", "Annualized Return", "Annualized Volatility", "Sharpe Ratio", "Max Drawdown"]
    values = [f"{stats[0]:.2%}", f"{stats[1]:.2%}", f"{stats[2]:.2%}", f"{stats[3]:.2f}", f"{stats[4]:.2%}"]
    for label, val in zip(labels, values):
        pdf.cell(50, 8, label, border=1)
        pdf.cell(40, 8, val, border=1, ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Growth of 100 (NAV Line)", ln=True)
    pdf.image(nav_plot_buf, x=10, y=None, w=180)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Monthly Returns History (Inc. YTD)", ln=True)
    pdf.set_font("Arial", '', 7)
    cols = list(pivot_table.columns)
    pdf.cell(15, 7, "Year", border=1, align='C')
    for col in cols:
        width = 15 if col == 'YTD' else 13
        pdf.cell(width, 7, col, border=1, align='C')
    pdf.ln()
    for year, row in pivot_table.iterrows():
        pdf.cell(15, 7, str(int(year)), border=1, align='C')
        for col in cols:
            val = row[col]
            width = 15 if col == 'YTD' else 13
            text = f"{val:.2%}" if not pd.isna(val) else "-"
            if col == 'YTD': pdf.set_font("Arial", 'B', 7)
            pdf.cell(width, 7, text, border=1, align='C')
            pdf.set_font("Arial", '', 7)
        pdf.ln()
    return bytes(pdf.output())


# --- 5. DATA LOADING ---
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
    df = df.dropna(subset=['Date'])
    df['Date'] = pd.to_datetime(df['Date'])
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df


uploaded_xlsx = st.sidebar.file_uploader("Upload Excel file", type=["xlsx"])
df = load_data(uploaded_xlsx)

if df is None:
    st.error("❌ Data file not found.")
    st.stop()

# --- 6. PERMISSIONS FILTERING ---
all_strategies = [col for col in df.columns if col != 'Date']
user_role = st.session_state["user_role"]
allowed_list = STRATEGY_GROUPS.get(user_role, [])

if allowed_list == "all":
    available_strategies = all_strategies
else:
    available_strategies = [s for s in all_strategies if s in allowed_list]

if not available_strategies:
    st.error("No strategies authorized for this account.")
    st.stop()

# --- 7. SIDEBAR FILTERS ---
st.sidebar.header(f"Role: {user_role.upper()}")
selected_strat = st.sidebar.selectbox("Select Strategy", available_strategies)

if st.sidebar.button("🔓 Log Out"):
    st.session_state["user_role"] = None
    st.rerun()

min_date, max_date = df['Date'].min(), df['Date'].max()
col1, col2 = st.sidebar.columns(2)
start_dt = col1.date_input("Start", min_date, min_value=min_date, max_value=max_date)
end_dt = col2.date_input("End", max_date, min_value=min_date, max_value=max_date)

mask = (df['Date'] >= pd.Timestamp(start_dt)) & (df['Date'] <= pd.Timestamp(end_dt))
subset = df.loc[mask, ['Date', selected_strat]].dropna().sort_values('Date')

if subset.empty:
    st.warning("No data found for this selection.")
    st.stop()

returns = subset[selected_strat].astype(float)


# --- 8. CALCULATIONS ---
def calc_metrics(r):
    cum_ret = (1 + r).prod() - 1
    ann_ret = (1 + cum_ret) ** (12 / len(r)) - 1 if len(r) > 0 else 0
    vol = r.std() * math.sqrt(12)
    sharpe = ann_ret / vol if vol != 0 else 0
    nav = (1 + r).cumprod()
    mdd = ((nav / nav.cummax()) - 1).min()
    return cum_ret, ann_ret, vol, sharpe, mdd


stats = calc_metrics(returns)

# --- 9. DISPLAY DASHBOARD ---
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total Return", f"{stats[0]:.2%}")
m2.metric("Ann. Return", f"{stats[1]:.2%}")
m3.metric("Ann. Vol", f"{stats[2]:.2%}")
m4.metric("Sharpe", f"{stats[3]:.2f}")
m5.metric("Max DD", f"{stats[4]:.2%}")

st.subheader(f"Growth of 100: {selected_strat}")
fig, ax = plt.subplots(figsize=(10, 4))
nav_series = (1 + returns).cumprod() * 100
ax.plot(subset['Date'], nav_series, color='#1f77b4', linewidth=2)
ax.fill_between(subset['Date'], nav_series, 100, alpha=0.1, color='#1f77b4')
ax.axhline(100, color='black', linestyle='--', alpha=0.3)
ax.grid(True, alpha=0.3)
st.pyplot(fig)

# --- MONTHLY TABLE WITH HIGHLIGHTED YTD ---
st.subheader("Monthly Returns & YTD")
subset['Year'] = subset['Date'].dt.year
subset['Month'] = subset['Date'].dt.strftime('%b')
pivot = subset.pivot(index='Year', columns='Month', values=selected_strat)
month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
pivot = pivot.reindex(columns=[m for m in month_order if m in pivot.columns])
pivot['YTD'] = pivot.apply(lambda row: (1 + row.dropna()).prod() - 1, axis=1)


def style_ytd(col):
    if col.name == 'YTD':
        return ['background-color: #e6f3ff; font-weight: bold'] * len(col)
    return [''] * len(col)


st.dataframe(pivot.style.apply(style_ytd).format("{:.2%}", na_rep="-"), use_container_width=True)

# --- 10. EXPORT PDF & METADATA ---
st.sidebar.markdown("---")

# FEATURE: Data Last Updated
last_data_point = df['Date'].max().strftime('%B %Y')
st.sidebar.info(f"📅 **Data through:** {last_data_point}")

if st.sidebar.button("🛠️ Prepare PDF Report"):
    img_buf = io.BytesIO()
    fig.savefig(img_buf, format="png", bbox_inches='tight', dpi=150)
    img_buf.seek(0)
    pdf_output = create_pdf(selected_strat, stats, img_buf, pivot)
    st.sidebar.download_button(
        label="📥 Download PDF",
        data=pdf_output,
        file_name=f"{selected_strat}_Report.pdf",
        mime="application/pdf"
    )

st.success(f"Access Granted: {user_role.upper()} View") 
