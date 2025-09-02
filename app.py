import io
import json
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

import mne
from mne.time_frequency import psd_welch

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# ---------------------------
# Page setup
# ---------------------------
st.set_page_config(page_title="EEG + Depression + Alzheimer (Demo)", layout="centered")
st.title("🧠 Early Risk Demo: EEG + Depression + Alzheimer (Cognitive)")

st.markdown(
    "Prototype for early screening by combining **EEG frequency bands**, **PHQ-2** (depression), "
    "and a short **AD8-style** memory/cognition questionnaire. "
    "_This is a research demo — not a medical device._"
)

# ---------------------------
# Helpers
# ---------------------------
BANDS = {
    "Delta (0.5–4 Hz)": (0.5, 4),
    "Theta (4–8 Hz)": (4, 8),
    "Alpha (8–12 Hz)": (8, 12),
    "Beta (12–30 Hz)": (12, 30),
    "Gamma (30–45 Hz)": (30, 45), # cap at 45 Hz for cleaner EDF demos
}

def bandpowers_from_raw(raw: mne.io.BaseRaw, fmax_cap: float = 45.0):
    """Compute band powers from MNE raw using Welch PSD and integrate bands."""
    # Use only EEG channels if present; else use all
    picks = mne.pick_types(raw.info, eeg=True, meg=False, eog=False, ecg=False, stim=False, exclude="bads")
    if len(picks) == 0:
        data = raw.get_data()
        sfreq = raw.info["sfreq"]
    else:
        data = raw.get_data(picks=picks)
        sfreq = raw.info["sfreq"]

    # Welch PSD
    psd, freqs = psd_welch(raw, fmin=0.5, fmax=fmax_cap, picks=picks if len(picks) > 0 else None,
                           n_fft=2048, n_overlap=1024, average="mean", verbose=False)
    # psd shape: (n_channels, n_freqs). Average channels
    if psd.ndim == 2:
        psd_mean = psd.mean(axis=0)
    else:
        psd_mean = psd # single channel

    band_powers = {}
    for band_name, (fmin, fmax) in BANDS.items():
        mask = (freqs >= fmin) & (freqs < fmax)
        if not np.any(mask):
            band_powers[band_name] = 0.0
        else:
            # integrate power over band
            band_powers[band_name] = float(np.trapz(psd_mean[mask], freqs[mask]))
    return band_powers, float(sfreq)

def raw_from_csv(file, sfreq: float):
    """Create MNE Raw from CSV (columns = channels)."""
    df = pd.read_csv(file)
    # Keep only numeric columns
    df = df.select_dtypes(include=[np.number])
    data = df.to_numpy().T # shape (n_channels, n_times)
    ch_names = [f"CH{i+1}" for i in range(data.shape[0])]
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types="eeg")
    raw = mne.io.RawArray(data, info, verbose=False)
    return raw

def make_band_bar_chart(band_powers: dict):
    """Return a PNG bytes buffer of a bar chart for band powers."""
    labels = list(band_powers.keys())
    values = [band_powers[k] for k in labels]

    fig, ax = plt.subplots(figsize=(6, 3.2), dpi=150)
    ax.bar(labels, values)
    ax.set_ylabel("Power (a.u.)")
    ax.set_title("EEG Band Powers (Welch PSD)")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf

def risk_from_ratios(band_powers: dict):
    """Compute simple demo ratios and qualitative flags."""
    alpha = band_powers.get("Alpha (8–12 Hz)", 1e-9)
    theta = band_powers.get("Theta (4–8 Hz)", 0.0)
    beta = band_powers.get("Beta (12–30 Hz)", 0.0)

    theta_alpha = float(theta / alpha) if alpha > 0 else 0.0
    beta_alpha = float(beta / alpha) if alpha > 0 else 0.0

    # Heuristic demo thresholds (NOT clinical!)
    dep_flag = "Higher" if theta_alpha > 0.8 else "Lower"
    ad_flag = "Possible concern" if beta_alpha < 0.5 else "Normal"

    return {
        "Theta/Alpha": round(theta_alpha, 3),
        "Beta/Alpha": round(beta_alpha, 3),
        "Depression (EEG heuristic)": dep_flag,
        "Alzheimer (EEG heuristic)": ad_flag,
    }

def generate_pdf(results: dict, band_plot_png: bytes | None):
    """Create a nicely formatted PDF with table and (optional) chart image."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    flow = []

    flow.append(Paragraph("🧠 Early Risk Demo Report", styles["Title"]))
    flow.append(Paragraph("EEG + Depression (PHQ-2) + AD8-style cognition", styles["Italic"]))
    flow.append(Spacer(1, 12))
    flow.append(Paragraph(f"Timestamp: {results['timestamp']}", styles["Normal"]))
    flow.append(Spacer(1, 12))

    # EEG table
    flow.append(Paragraph("<b>EEG Summary</b>", styles["Heading3"]))
    eeg_rows = [["Metric", "Value"]]
    eeg = results["EEG"]
    eeg_rows += [
        ["File name", eeg.get("filename", "—")],
        ["File size (MB)", eeg.get("filesize_mb", "—")],
        ["Sampling rate (Hz)", eeg.get("sfreq_hz", "—")],
    ]
    for k, v in eeg["bands"].items():
        eeg_rows.append([k, f"{v:.4f}"])
    eeg_rows.append(["Theta/Alpha", results["EEG"]["ratios"]["Theta/Alpha"]])
    eeg_rows.append(["Beta/Alpha", results["EEG"]["ratios"]["Beta/Alpha"]])

    table = Table(eeg_rows, colWidths=[180, 320])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("BOX", (0,0), (-1,-1), 0.5, colors.grey),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("ALIGN", (1,1), (-1,-1), "LEFT"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
    ]))
    flow.append(table)
    flow.append(Spacer(1, 10))

    if band_plot_png is not None:
        img = RLImage(io.BytesIO(band_plot_png), width=420, height=220) # scaled
        flow.append(Spacer(1, 6))
        flow.append(img)
        flow.append(Spacer(1, 6))

    # Questionnaires
    flow.append(Paragraph("<b>Depression (PHQ-2)</b>", styles["Heading3"]))
    flow.append(Paragraph(f"Score: {results['Depression']['score']} / 6", styles["Normal"]))
    flow.append(Paragraph(f"Risk: {results['Depression']['risk']}", styles["Normal"]))
    flow.append(Spacer(1, 8))

    flow.append(Paragraph("<b>Alzheimer (AD8-style demo)</b>", styles["Heading3"]))
    flow.append(Paragraph(f"Score: {results['Alzheimer']['score']} / 8", styles["Normal"]))
    flow.append(Paragraph(f"Risk: {results['Alzheimer']['risk']}", styles["Normal"]))
    flow.append(Spacer(1, 8))

    # Combined (demo)
    flow.append(Paragraph("<b>Combined Early Risk (demo)</b>", styles["Heading3"]))
    flow.append(Paragraph(results["combined_note"], styles["Normal"]))
    flow.append(Spacer(1, 12))

    flow.append(Paragraph(
        "Disclaimer: This report is a research <i>demo</i>. It is not a clinical diagnosis or medical advice.",
        styles["Normal"]
    ))

    doc.build(flow)
    buf.seek(0)
    return buf

# ---------------------------
# EEG Upload & Processing
# ---------------------------
st.header("1) EEG Upload & Frequency Analysis")

uploaded = st.file_uploader("Upload EEG file (.edf or .csv)", type=["edf", "csv"])
sfreq_csv = None
raw = None
eeg_info = {"filename": None, "filesize_mb": None, "sfreq_hz": None}
band_powers = {}
ratios = {}
band_chart_buf = None

if uploaded is not None:
    eeg_info["filename"] = uploaded.name
    uploaded_bytes = uploaded.getbuffer()
    eeg_info["filesize_mb"] = round(len(uploaded_bytes) / (1024 * 1024), 3)

    if uploaded.name.lower().endswith(".edf"):
        try:
            raw = mne.io.read_raw_edf(io.BytesIO(uploaded_bytes), preload=True, verbose=False)
            band_powers, sf = bandpowers_from_raw(raw)
            eeg_info["sfreq_hz"] = sf
        except Exception as e:
            st.error(f"Could not read EDF: {e}")
    else:
        # CSV path: user supplies sampling rate
        sfreq_csv = st.number_input("Sampling rate (Hz) for CSV", min_value=50, max_value=2000, value=256, step=1)
        if sfreq_csv:
            try:
                raw = raw_from_csv(io.BytesIO(uploaded_bytes), sfreq_csv)
                band_powers, sf = bandpowers_from_raw(raw)
                eeg_info["sfreq_hz"] = sf
            except Exception as e:
                st.error(f"Could not parse CSV: {e}")

    # If we got powers, show chart
    if band_powers:
        st.subheader("EEG Band Powers (Welch PSD)")
        df_bands = pd.DataFrame({"Band": list(band_powers.keys()), "Power": list(band_powers.values())})
        st.bar_chart(df_bands.set_index("Band"))
        ratios = risk_from_ratios(band_powers)
        st.write(f"**Theta/Alpha**: {ratios['Theta/Alpha']} | **Beta/Alpha**: {ratios['Beta/Alpha']}")
        st.caption(f"EEG heuristics → Depression: {ratios['Depression (EEG heuristic)']}, "
                   f"Alzheimer: {ratios['Alzheimer (EEG heuristic)']}")

        # Prepare chart for PDF
        band_chart_buf = make_band_bar_chart(band_powers).getvalue()

# ---------------------------
# PHQ-2 (Depression)
# ---------------------------
st.header("2) Depression Screening (PHQ-2)")

phq_options = ["0 = Not at all", "1 = Several days", "2 = More than half the days", "3 = Nearly every day"]
phq_q1 = st.selectbox("Little interest or pleasure in doing things?", phq_options, index=0)
phq_q2 = st.selectbox("Feeling down, depressed, or hopeless?", phq_options, index=0)

phq_map = {opt: int(opt.split("=")[0].strip()) for opt in phq_options}
phq_score = phq_map[phq_q1] + phq_map[phq_q2]
phq_risk = "High (≥3 → further eval recommended)" if phq_score >= 3 else "Low"

st.write(f"**PHQ-2 Score:** {phq_score} / 6 → **Risk:** {phq_risk}")

# ---------------------------
# AD8-style (Alzheimer demo)
# ---------------------------
st.header("3) Alzheimer Screening (AD8-style demo)")
st.caption("Answer Yes/No based on changes noticed over the last few years.")

ad8_items = [
    "Problems with judgment (e.g., bad financial decisions)?",
    "Reduced interest in hobbies/activities?",
    "Repeats the same questions/stories over and over?",
    "Trouble learning how to use a tool/appliance/gadget?",
    "Forgets the correct month or year?",
    "Difficulty handling complex tasks (e.g., budgeting)?",
    "Forgets appointments?",
    "Everyday thinking is getting worse?"
]
ad8_answers = []
for i, item in enumerate(ad8_items, start=1):
    ans = st.selectbox(f"AD8-{i}: {item}", ["No", "Yes"], index=0, key=f"ad8_{i}")
    ad8_answers.append(ans)

ad8_score = sum(1 for a in ad8_answers if a == "Yes") # Yes=1
ad8_risk = "Possible concern (≥2 suggests cognitive impairment)" if ad8_score >= 2 else "Low"
st.write(f"**AD8-style Score:** {ad8_score} / 8 → **Risk:** {ad8_risk}")

# ---------------------------
# Build results + downloads
# ---------------------------
st.header("4) Generate Reports (PDF & JSON)")
if st.button("Create Reports"):
    if uploaded is None:
        st.warning("Please upload an EEG file first.")
    else:
        results = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "EEG": {
                "filename": eeg_info["filename"],
                "filesize_mb": eeg_info["filesize_mb"],
                "sfreq_hz": eeg_info["sfreq_hz"],
                "bands": band_powers,
                "ratios": ratios
            },
            "Depression": {
                "phq2": {"Q1": phq_q1, "Q2": phq_q2},
                "score": phq_score,
                "risk": phq_risk
            },
            "Alzheimer": {
                "ad8_answers": dict(zip([f"AD8-{i+1}" for i in range(len(ad8_items))], ad8_answers)),
                "score": ad8_score,
                "risk": ad8_risk
            },
            # Combined demo note (NOT clinical)
            "combined_note": (
                "Demo synthesis → EEG Theta/Alpha & Beta/Alpha + PHQ-2 + AD8-style. "
                "High PHQ-2 (≥3) or AD8 (≥2) or EEG heuristic flags may warrant further evaluation. "
                "This is NOT a diagnosis."
            )
        }

        # JSON download
        json_bytes = io.BytesIO(json.dumps(results, indent=2).encode("utf-8"))
        st.download_button("⬇️ Download JSON", data=json_bytes, file_name="early_risk_report.json")

        # PDF download
        pdf_buf = generate_pdf(results, band_chart_buf)
        st.download_button("⬇️ Download PDF", data=pdf_buf, file_name="early_risk_report.pdf", mime="application/pdf")

st.caption("© Research demo. No clinical use.")
