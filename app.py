import streamlit as st
import numpy as np
import json
import io
from mne.io import read_raw_edf
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from datetime import datetime

# -------------------------
# Helper: Generate PDF Report
# -------------------------
def generate_pdf(result_data):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Title
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(colors.darkblue)
    c.drawString(100, height - 80, "EEG-based Depression & Cognitive Assessment Report")

    # Date
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(100, height - 100, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Section: EEG Analysis
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 150, "EEG Analysis Result")
    c.setFont("Helvetica", 12)
    c.drawString(120, height - 170, f"EEG Depression Risk Score: {result_data['eeg_score']} / 100")

    # Section: Questionnaire
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 220, "Mood & Sleep Questionnaire")
    c.setFont("Helvetica", 12)
    c.drawString(120, height - 240, f"Questionnaire Score: {result_data['questionnaire_score']} / 100")

    # Section: Cognitive Test
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 290, "Cognitive Test Result")
    c.setFont("Helvetica", 12)
    c.drawString(120, height - 310, f"Cognitive Score: {result_data['cognitive_score']} / 100")

    # Final Index
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 360, "Final Risk Index")
    c.setFont("Helvetica", 12)
    c.drawString(120, height - 380, f"Combined Risk Index: {result_data['final_index']} / 100")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# -------------------------
# Streamlit App
# -------------------------
st.title("🧠 EEG-based Depression Detection & Cognitive Assessment")

# Upload EEG
uploaded_file = st.file_uploader("Upload your EEG file (.edf)", type=["edf"])

if uploaded_file is not None:
    # Read EEG safely
    raw = read_raw_edf(io.BytesIO(uploaded_file.read()), preload=True, verbose=False)
    data, times = raw[:]
    eeg_score = float(np.mean(np.abs(data[0]))) * 100
    eeg_score = min(max(int(eeg_score), 0), 100)

    st.success("EEG file uploaded successfully ✅")
    st.write(f"EEG Depression Risk Score: **{eeg_score}/100**")
else:
    eeg_score = 50 # default demo

# Questionnaire
st.subheader("📝 Mood & Sleep Questionnaire")
q1 = st.slider("Over the last 2 weeks, how often have you felt little interest or pleasure in doing things?", 0, 3, 1)
q2 = st.slider("Over the last 2 weeks, how often have you had trouble sleeping?", 0, 3, 1)
questionnaire_score = (q1 + q2) * 20

# Cognitive Test (simple reaction time test)
st.subheader("🧩 Cognitive Test (Demo)")
cog_input = st.number_input("Type a number quickly (demo cognitive task)", 0, 100, 50)
cognitive_score = 100 - abs(50 - cog_input)

# Final Index
final_index = int((eeg_score + questionnaire_score + cognitive_score) / 3)

st.subheader("📊 Final Risk Index")
st.write(f"**{final_index}/100**")

# Collect results
results = {
    "eeg_score": eeg_score,
    "questionnaire_score": questionnaire_score,
    "cognitive_score": cognitive_score,
    "final_index": final_index,
    "timestamp": datetime.now().isoformat()
}

# Export JSON
json_bytes = io.BytesIO(json.dumps(results, indent=4).encode("utf-8"))
st.download_button("⬇️ Download Results (JSON)", data=json_bytes, file_name="results.json")

# Export PDF
pdf_file = generate_pdf(results)
st.download_button("⬇️ Download Report (PDF)", data=pdf_file, file_name="results_report.pdf", mime="application/pdf")


# 🧠 EEG-based Depression & Cognitive Assessment

This project is a **prototype web app** built with [Streamlit](https://streamlit.io/) that combines:

- **EEG analysis** (from `.edf` files) using [MNE-Python](https://mne.tools/)
- **Questionnaire** about mood & sleep
- **Cognitive test** (demo task)
- **Final Risk Index** that integrates all results

The app generates **PDF reports** (for clinicians/researchers) and **JSON outputs** (for data analysis)
