import streamlit as st
import mne
import numpy as np
import matplotlib.pyplot as plt
import tempfile
import json
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet

# ---------- محاسبه باندهای فرکانسی ----------
def compute_band_powers(raw):
    psds, freqs = mne.time_frequency.psd_welch(raw, fmin=0.5, fmax=40, n_fft=2048)
    psd_mean = np.mean(psds, axis=0)

    bands = {
        "Delta (0.5-4 Hz)": (0.5, 4),
        "Theta (4-8 Hz)": (4, 8),
        "Alpha (8-12 Hz)": (8, 12),
        "Beta (12-30 Hz)": (12, 30),
        "Gamma (30-40 Hz)": (30, 40),
    }

    band_powers = {}
    for band, (low, high) in bands.items():
        idx = np.logical_and(freqs >= low, freqs <= high)
        band_powers[band] = float(np.mean(psd_mean[idx]))

    return band_powers


# ---------- تولید گزارش ----------
def generate_reports(results):
    # ذخیره JSON
    with open("report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    # ذخیره PDF
    doc = SimpleDocTemplate("report.pdf")
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("گزارش تحلیل EEG و پرسشنامه‌ها", styles["Title"]))
    elements.append(Spacer(1, 12))

    for key, value in results.items():
        if isinstance(value, dict):
            elements.append(Paragraph(f"<b>{key}</b>", styles["Heading2"]))
            for k, v in value.items():
                elements.append(Paragraph(f"{k}: {v}", styles["Normal"]))
        else:
            elements.append(Paragraph(f"{key}: {value}", styles["Normal"]))
        elements.append(Spacer(1, 12))

    doc.build(elements)


# ---------- اپلیکیشن ----------
st.title("🧠 Depression & Alzheimer Assessment (Demo)")

results = {}

# ---- EEG Upload ----
uploaded_file = st.file_uploader("Upload your EEG file (.edf)", type=["edf"])
if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".edf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    raw = mne.io.read_raw_edf(tmp_path, preload=True, verbose=False)
    band_powers = compute_band_powers(raw)
    results["EEG Band Powers"] = band_powers

    st.subheader("📊 EEG Frequency Bands")
    fig, ax = plt.subplots()
    ax.bar(band_powers.keys(), band_powers.values())
    plt.xticks(rotation=45)
    st.pyplot(fig)


# ---- پرسشنامه افسردگی (PHQ-9 ساده) ----
st.subheader("📝 Depression Questionnaire (PHQ-9)")
phq_score = 0
phq_questions = [
    "1. Little interest or pleasure in doing things?",
    "2. Feeling down, depressed, or hopeless?",
    "3. Trouble sleeping or sleeping too much?",
    "4. Feeling tired or little energy?",
    "5. Poor appetite or overeating?",
    "6. Feeling bad about yourself?",
    "7. Trouble concentrating?",
    "8. Moving or speaking slowly / fidgety?",
    "9. Thoughts of self-harm?",
]

for q in phq_questions:
    phq_score += st.radio(q, [0, 1, 2, 3], horizontal=True, key=q)

results["Depression Score (PHQ-9)"] = phq_score
if phq_score < 5:
    results["Depression Severity"] = "Minimal"
elif phq_score < 10:
    results["Depression Severity"] = "Mild"
elif phq_score < 15:
    results["Depression Severity"] = "Moderate"
else:
    results["Depression Severity"] = "Severe"


# ---- پرسشنامه آلزایمر (Mini-Cog ساده) ----
st.subheader("📝 Alzheimer Screening (Mini-Cog)")
alz_score = 0
alz_q1 = st.radio("1. What year is it?", ["Wrong", "Correct"])
alz_score += 1 if alz_q1 == "Correct" else 0

alz_q2 = st.radio("2. What month is it?", ["Wrong", "Correct"])
alz_score += 1 if alz_q2 == "Correct" else 0

alz_q3 = st.radio("3. Recall the word 'APPLE' after a few seconds", ["Wrong", "Correct"])
alz_score += 1 if alz_q3 == "Correct" else 0

results["Alzheimer Score"] = alz_score
results["Alzheimer Risk"] = "Possible Impairment" if alz_score < 2 else "Low Risk"


# ---- تولید گزارش ----
if st.button("📑 Generate Report"):
    generate_reports(results)
    st.success("Report generated: report.pdf & report.json")
    st.json(results)
