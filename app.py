import streamlit as st
import mne
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet


# -----------------------------
# تابع محاسبه باندهای فرکانسی EEG
# -----------------------------
def compute_band_powers(raw):
    psds, freqs = mne.time_frequency.psd_welch(raw, fmin=0.5, fmax=50, n_fft=1024)
    psds = np.mean(psds, axis=0)

    bands = {
        "Delta (0.5–4 Hz)": (0.5, 4),
        "Theta (4–8 Hz)": (4, 8),
        "Alpha (8–12 Hz)": (8, 12),
        "Beta (12–30 Hz)": (12, 30),
        "Gamma (30–50 Hz)": (30, 50),
    }

    band_powers = {}
    for band, (fmin, fmax) in bands.items():
        idx = np.logical_and(freqs >= fmin, freqs <= fmax)
        band_powers[band] = np.mean(psds[idx])

    return band_powers


# -----------------------------
# تولید PDF گزارش
# -----------------------------
def generate_pdf(report_data, band_powers, fig_path):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>EEG-based Depression & Alzheimer Assessment</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Frequency Band Powers:</b>", styles["Heading2"]))
    for band, value in band_powers.items():
        story.append(Paragraph(f"{band}: {value:.4f}", styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Questionnaire Results:</b>", styles["Heading2"]))
    for key, value in report_data.items():
        story.append(Paragraph(f"{key}: {value}", styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>EEG Frequency Plot:</b>", styles["Heading2"]))
    story.append(Image(fig_path, width=400, height=200))

    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data


# -----------------------------
# Streamlit Interface
# -----------------------------
st.title("🧠 EEG-based Depression & Alzheimer Assessment (Demo)")

# EEG Upload
uploaded_file = st.file_uploader("Upload your EEG file (.edf)", type=["edf"])

band_powers = None
if uploaded_file:
    raw = mne.io.read_raw_edf(uploaded_file, preload=True, verbose=False)
    band_powers = compute_band_powers(raw)

    # رسم نمودار
    fig, ax = plt.subplots()
    ax.bar(band_powers.keys(), band_powers.values())
    plt.xticks(rotation=45)
    plt.title("EEG Frequency Bands")
    fig_path = "bands_plot.png"
    plt.savefig(fig_path)
    st.pyplot(fig)


# -----------------------------
# Depression Questionnaire
# -----------------------------
st.header("📝 Depression Questionnaire (PHQ-9 style)")
q1 = st.radio("Over the last 2 weeks, little interest or pleasure in doing things?", ["Not at all", "Several days", "More than half the days", "Nearly every day"])
q2 = st.radio("Over the last 2 weeks, feeling down, depressed, or hopeless?", ["Not at all", "Several days", "More than half the days", "Nearly every day"])

# -----------------------------
# Alzheimer Questionnaire
# -----------------------------
st.header("🧩 Alzheimer Screening Questions")
a1 = st.radio("Do you often forget recent events?", ["Never", "Sometimes", "Often", "Always"])
a2 = st.radio("Do you have trouble finding words during conversation?", ["Never", "Sometimes", "Often", "Always"])

# -----------------------------
# Generate Report
# -----------------------------
if st.button("Generate Report (PDF + JSON)"):
    report_data = {
        "Depression Q1": q1,
        "Depression Q2": q2,
        "Alzheimer Q1": a1,
        "Alzheimer Q2": a2,
    }

    if band_powers:
        # PDF
        pdf_data = generate_pdf(report_data, band_powers, fig_path)
        st.download_button("📥 Download PDF Report", data=pdf_data, file_name="EEG_Report.pdf", mime="application/pdf")

        # JSON
        output = {"Bands": band_powers, "Questionnaires": report_data}
        json_data = json.dumps(output, indent=4)
        st.download_button("📥 Download JSON Report", data=json_data, file_name="EEG_Report.json", mime="application/json")
    else:
        st.warning("Please upload an EEG file first.")
