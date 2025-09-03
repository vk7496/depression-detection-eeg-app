import io
import os
import json
import tempfile
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import mne

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="EEG + Depression + Alzheimer (Demo)", layout="centered")
st.title("🧠 EEG-based Depression & Alzheimer Assessment (Demo)")
st.caption("Research prototype — not a medical device or diagnosis.")

# -----------------------------
# Helpers
# -----------------------------
BANDS = {
    "Delta (0.5–4 Hz)": (0.5, 4),
    "Theta (4–8 Hz)": (4, 8),
    "Alpha (8–12 Hz)": (8, 12),
    "Beta (12–30 Hz)": (12, 30),
    "Gamma (30–45 Hz)": (30, 45),
}


def compute_band_powers_from_raw(raw: mne.io.BaseRaw, fmin=0.5, fmax=45.0):
    """Welch PSD (MNE >=1.6 via raw.compute_psd), average across channels, integrate bands."""
    psd = raw.compute_psd(method="welch", fmin=fmin, fmax=fmax, n_fft=2048, n_overlap=1024, verbose=False)
    psds, freqs = psd.get_data(return_freqs=True) # shape: (n_channels, n_freqs)
    psd_mean = psds.mean(axis=0) if psds.ndim == 2 else psds

    band_powers = {}
    for name, (lo, hi) in BANDS.items():
        mask = (freqs >= lo) & (freqs < hi)
        band_powers[name] = float(np.trapz(psd_mean[mask], freqs[mask])) if mask.any() else 0.0
    return band_powers, freqs


def make_band_chart_png(band_powers: dict) -> bytes:
    labels = list(band_powers.keys())
    values = [band_powers[k] for k in labels]
    fig, ax = plt.subplots(figsize=(6, 3), dpi=150)
    ax.bar(labels, values)
    ax.set_title("EEG Band Powers (Welch PSD)")
    ax.set_ylabel("Power (a.u.)")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def make_signal_snippet_png(raw: mne.io.BaseRaw, seconds=10) -> bytes:
    data = raw.get_data(picks=mne.pick_types(raw.info, eeg=True)) # (n_ch, n_times)
    if data.ndim == 2:
        ch0 = data[0]
    else:
        ch0 = data
    sf = raw.info["sfreq"]
    n = int(min(len(ch0), seconds * sf))
    t = np.arange(n) / sf

    fig, ax = plt.subplots(figsize=(6, 2.5), dpi=150)
    ax.plot(t, ch0[:n])
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("µV (a.u.)")
    ax.set_title(f"EEG First Channel — {min(seconds, n/sf):.1f}s snippet")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def eeg_heuristics(band_powers: dict):
    alpha = band_powers.get("Alpha (8–12 Hz)", 1e-9)
    theta = band_powers.get("Theta (4–8 Hz)", 0.0)
    beta = band_powers.get("Beta (12–30 Hz)", 0.0)
    theta_alpha = float(theta / alpha) if alpha > 0 else 0.0
    beta_alpha = float(beta / alpha) if alpha > 0 else 0.0
    return {
        "Theta/Alpha": round(theta_alpha, 3),
        "Beta/Alpha": round(beta_alpha, 3),
        "Depression (EEG heuristic)": "Higher" if theta_alpha > 0.8 else "Lower",
        "Alzheimer (EEG heuristic)": "Possible concern" if beta_alpha < 0.5 else "Normal",
    }


def build_pdf(results: dict, band_png: bytes | None, sig_png: bytes | None) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    flow = []

    flow.append(Paragraph("🧠 Early Cognitive Risk Report", styles["Title"]))
    flow.append(Paragraph("EEG + PHQ-2 (depression) + AD8-style (cognition)", styles["Italic"]))
    flow.append(Spacer(1, 10))
    flow.append(Paragraph(f"Timestamp: {results['timestamp']}", styles["Normal"]))
    flow.append(Spacer(1, 10))

    # EEG table
    flow.append(Paragraph("<b>EEG Summary</b>", styles["Heading3"]))
    rows = [["Metric", "Value"]]
    eeg = results["EEG"]
    rows += [
        ["File", eeg["filename"]],
        ["Filesize (MB)", eeg["filesize_mb"]],
        ["Sampling rate (Hz)", eeg.get("sfreq_hz", "—")],
    ]
    for k, v in eeg["bands"].items():
        rows.append([k, f"{v:.5f}"])
    rows.append(["Theta/Alpha", eeg["ratios"]["Theta/Alpha"]])
    rows.append(["Beta/Alpha", eeg["ratios"]["Beta/Alpha"]])

    table = Table(rows, colWidths=[170, 340])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("BOX", (0,0), (-1,-1), 0.5, colors.grey),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("FONTSIZE", (0,0), (-1,-1), 9),
    ]))
    flow.append(table)
    flow.append(Spacer(1, 8))

    if band_png:
        flow.append(Spacer(1, 4))
        flow.append(RLImage(io.BytesIO(band_png), width=420, height=200))
    if sig_png:
        flow.append(Spacer(1, 8))
        flow.append(RLImage(io.BytesIO(sig_png), width=420, height=180))

    # PHQ-2
    flow.append(Spacer(1, 10))
    flow.append(Paragraph("<b>Depression (PHQ-2)</b>", styles["Heading3"]))
    flow.append(Paragraph(f"Score: {results['Depression']['score']} / 6", styles["Normal"]))
    flow.append(Paragraph(f"Risk: {results['Depression']['risk']}", styles["Normal"]))

    # AD8-style
    flow.append(Spacer(1, 10))
    flow.append(Paragraph("<b>Alzheimer (AD8-style)</b>", styles["Heading3"]))
    flow.append(Paragraph(f"Score: {results['Alzheimer']['score']} / 8", styles["Normal"]))
    flow.append(Paragraph(f"Risk: {results['Alzheimer']['risk']}", styles["Normal"]))

    flow.append(Spacer(1, 12))
    flow.append(Paragraph(
        "Disclaimer: Research demo. Not for clinical use.", styles["Normal"]
    ))

    doc.build(flow)
    buf.seek(0)
    return buf.getvalue()


# -----------------------------
# 1) EEG Upload & Analysis
# -----------------------------
st.header("1) Upload EEG (.edf) and Analyze")
uploaded = st.file_uploader("Upload your EEG file (EDF)", type=["edf"])
raw = None
band_powers, ratios = {}, {}
band_png = sig_png = None
eeg_meta = {"filename": None, "filesize_mb": None, "sfreq_hz": None}

if uploaded is not None:
    eeg_meta["filename"] = uploaded.name
    eeg_meta["filesize_mb"] = round(len(uploaded.getbuffer()) / (1024 * 1024), 3)
    # save to temp and read with MNE
    with tempfile.NamedTemporaryFile(delete=False, suffix=".edf") as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name
    raw = mne.io.read_raw_edf(tmp_path, preload=True, verbose=False)
    eeg_meta["sfreq_hz"] = float(raw.info["sfreq"])

    # Compute band powers
    band_powers, _ = compute_band_powers_from_raw(raw)
    ratios = eeg_heuristics(band_powers)

    # Show charts in app
    st.subheader("EEG Band Powers")
    df_bands = pd.DataFrame({"Band": list(band_powers.keys()), "Power": list(band_powers.values())})
    st.bar_chart(df_bands.set_index("Band"))
    st.caption(f"Theta/Alpha = {ratios['Theta/Alpha']} | Beta/Alpha = {ratios['Beta/Alpha']}")

    # Show raw snippet plot
    st.subheader("EEG Signal Snippet (first channel, ~10s)")
    sig_png = make_signal_snippet_png(raw)
    st.image(sig_png, use_column_width=True)

    # Prepare band bar png for PDF
    band_png = make_band_chart_png(band_powers)

# -----------------------------
# 2) Depression – PHQ-2
# -----------------------------
st.header("2) Depression Screening (PHQ-2)")
phq_opts = ["0 = Not at all", "1 = Several days", "2 = More than half the days", "3 = Nearly every day"]
q1 = st.selectbox("Little interest or pleasure in doing things?", phq_opts, index=0)
q2 = st.selectbox("Feeling down, depressed, or hopeless?", phq_opts, index=0)
map_phq = {opt: int(opt.split("=")[0].strip()) for opt in phq_opts}
phq_score = map_phq[q1] + map_phq[q2]
phq_risk = "High (≥3 → follow-up recommended)" if phq_score >= 3 else "Low"
st.write(f"**PHQ-2 Score:** {phq_score} / 6 → **{phq_risk}**")

# -----------------------------
# 3) Alzheimer – AD8-style (short)
# -----------------------------
st.header("3) Alzheimer Screening (AD8-style)")
ad8_items = [
    "Problems with judgment (e.g., bad financial decisions)?",
    "Reduced interest in hobbies/activities?",
    "Repeats the same questions/stories?",
    "Trouble learning to use tools/appliances?",
    "Forgets the correct month or year?",
    "Difficulty handling complex tasks (e.g., bills)?",
    "Forgets appointments?",
    "Everyday thinking is getting worse?",
]
ad8_answers = []
for i, it in enumerate(ad8_items, 1):
    ad8_answers.append(st.selectbox(f"AD8-{i}: {it}", ["No", "Yes"], index=0, key=f"ad8_{i}"))
ad8_score = sum(1 for a in ad8_answers if a == "Yes")
ad8_risk = "Possible concern (≥2 suggests impairment)" if ad8_score >= 2 else "Low"
st.write(f"**AD8 Score:** {ad8_score} / 8 → **{ad8_risk}**")

# -----------------------------
# 4) Create Reports
# -----------------------------
st.header("4) Generate Reports (PDF & JSON)")
if st.button("Create Reports"):
    if uploaded is None or raw is None:
        st.warning("Please upload an EEG file first.")
    else:
        results = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "EEG": {
                "filename": eeg_meta["filename"],
                "filesize_mb": eeg_meta["filesize_mb"],
                "sfreq_hz": eeg_meta["sfreq_hz"],
                "bands": band_powers,
                "ratios": ratios,
            },
            "Depression": {
                "score": phq_score,
                "risk": phq_risk,
                "answers": {"Q1": q1, "Q2": q2},
            },
            "Alzheimer": {
                "score": ad8_score,
                "risk": ad8_risk,
                "answers": dict(zip([f"AD8-{i+1}" for i in range(len(ad8_items))], ad8_answers)),
            },
            "note": "Demo synthesis of EEG heuristics + PHQ-2 + AD8-style. Not a diagnosis.",
        }

        # JSON
        json_bytes = io.BytesIO(json.dumps(results, indent=2).encode("utf-8"))
        st.download_button("⬇️ Download JSON", data=json_bytes, file_name="report.json", mime="application/json")

        # PDF
        pdf_bytes = build_pdf(results, band_png, sig_png)
        st.download_button("⬇️ Download PDF", data=pdf_bytes, file_name="report.pdf", mime="application/pdf")

st.caption("© Demo for research/competition purposes only.")
