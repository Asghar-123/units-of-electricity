import streamlit as st
import pandas as pd
from datetime import datetime
import os
from fpdf import FPDF
import base64

# === SETUP ===
DATA_DIR = "readings"
os.makedirs(DATA_DIR, exist_ok=True)

def get_month_key(selected_date):
    return selected_date.strftime("%Y-%m")

def get_month_file(month_key):
    return os.path.join(DATA_DIR, f"{month_key}.csv")

def get_pdf_file(month_key):
    return os.path.join(DATA_DIR, f"{month_key}-summary.pdf")

def load_data(month_key):
    file_path = get_month_file(month_key)
    if os.path.exists(file_path):
        return pd.read_csv(file_path, parse_dates=["date"])
    else:
        return pd.DataFrame(columns=["date", "time", "meter_reading", "difference", "razi", "zaki"])

def save_data(df, month_key):
    df.to_csv(get_month_file(month_key), index=False)

def generate_pdf(df, month_key):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, f"Electricity Usage Report - {month_key}", ln=True, align="C")

    pdf.set_font("Arial", "B", 10)
    col_widths = [30, 25, 30, 25, 25, 25]
    headers = ["Date", "Time", "Meter Reading", "Difference", "Razi", "Zaki"]
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, border=1)
    pdf.ln()

    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        values = [row["date"], row["time"], row["meter_reading"], row["difference"], row["razi"], row["zaki"]]
        for i, val in enumerate(values):
            pdf.cell(col_widths[i], 8, str(val), border=1)
        pdf.ln()

    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, f"Total Units: {df['difference'].sum():.2f}", ln=True)
    pdf.cell(200, 10, f"Razi's Total: {df['razi'].sum():.2f}", ln=True)
    pdf.cell(200, 10, f"Zaki's Total: {df['zaki'].sum():.2f}", ln=True)

    pdf.output(get_pdf_file(month_key))

def get_pdf_download_link(pdf_path):
    with open(pdf_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")
        href = f'<a href="data:application/octet-stream;base64,{base64_pdf}" download="{os.path.basename(pdf_path)}">📥 Download PDF Report</a>'
        return href

# === STREAMLIT APP ===
st.set_page_config(page_title="Monthly Unit Tracker", layout="wide")
st.title("⚡ Monthly Electricity Unit Tracker")

# Sidebar Month Selector
st.sidebar.header("📁 Month Selector")
selected_date = st.sidebar.date_input("Select Month", datetime.today())
month_key = get_month_key(selected_date)
st.sidebar.write(f"Selected: **{month_key}**")

# Load monthly data
df = load_data(month_key)

# === FORM ===
st.subheader("➕ Add New Reading")
with st.form("reading_form"):
    date = st.date_input("Date", datetime.today())
    time = st.time_input("Time", datetime.now().time())
    meter_reading = st.number_input("Meter Reading", min_value=0.0, step=0.1)

    previous_reading = df["meter_reading"].iloc[-1] if not df.empty else 0.0
    difference = meter_reading - previous_reading if previous_reading else 0.0

    if previous_reading:
        st.info(f"📉 Previous Reading: {previous_reading}")
        st.success(f"⚙️ Difference: {difference:.2f}")
    else:
        st.warning("No previous data found. This will be the starting point.")

    razi = st.number_input("Razi's Units", min_value=0.0, step=0.1)
    zaki = st.number_input("Zaki's Units", min_value=0.0, step=0.1)

    submitted = st.form_submit_button("✅ Submit")
    if submitted:
        new_entry = {
            "date": date.strftime("%Y-%m-%d"),
            "time": time.strftime("%H:%M:%S"),
            "meter_reading": meter_reading,
            "difference": difference,
            "razi": razi,
            "zaki": zaki,
        }
        df = df._append(new_entry, ignore_index=True)
        save_data(df, month_key)
        st.success("Reading saved successfully!")

# === DATA TABLE ===
st.subheader("📊 Editable Monthly Data")
edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
if st.button("💾 Save Changes"):
    save_data(edited_df, month_key)
    st.success("Changes saved successfully!")

# === METRICS ===
if not df.empty:
    st.metric("🔢 Total Units Used", f"{df['difference'].sum():.2f} kWh")
    st.bar_chart(df[["razi", "zaki"]])

# === RESET OPTION ===
st.subheader("🧹 Reset Data")
if st.button("❌ Reset This Month"):
    df = pd.DataFrame(columns=["date", "time", "meter_reading", "difference", "razi", "zaki"])
    save_data(df, month_key)
    st.warning(f"Data for {month_key} has been reset.")

# === CLOSE MONTH ===
st.subheader("🔐 Close Month & Generate PDF")
if st.button("📄 Close & Generate Report"):
    if not df.empty:
        generate_pdf(df, month_key)
        st.success(f"Report for {month_key} generated successfully.")
        st.markdown(get_pdf_download_link(get_pdf_file(month_key)), unsafe_allow_html=True)
    else:
        st.warning("⚠️ No data to generate PDF.")