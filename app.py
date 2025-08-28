import streamlit as st
import mne
import numpy as np
import json
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

# -------------------
# Simulated Prediction (dummy model)
# -------------------
def predict_depression(features):
    # Just a placeholder function
    score = np.mean(list(features.values()))
    if score < 0.3:
        return "No Depression", score
    elif score < 0.6:
        return "Mild Depression", score
    else:
        return "Severe Depression", score

# -------------------
# Feature Extraction (simplified)
# -------------------
def extract_features(raw):
    data = raw.get_data()
    psd, freqs = mne.time_frequency.psd_array_welch(
        data, sfreq=raw.info["sfreq"], fmin=1, fmax=50, n_fft=256
    )

    features = {
        "delta_power": float(np.mean(psd[:, (freqs >= 1) & (freqs < 4)])),
        "theta_power": float(np.mean(psd[:, (freqs >= 4) & (freqs < 8)])),
        "alpha_power": float(np.mean(psd[:, (freqs >= 8) & (freqs < 13)])),
        "beta_power": float(np.mean(psd[:, (freqs >= 13) & (freqs < 30)])),
    }
    return features

# -------------------
# Report (PDF)
# -------------------
def generate_pdf_report(result, score, features, sfreq, nchan, ch_names):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Depression Detection Report", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Prediction: {result}", styles["Normal"]))
    elements.append(Paragraph(f"Score: {score:.2f}", styles["Normal"]))
    elements.append(Paragraph(f"Sampling rate: {sfreq} Hz", styles["Normal"]))
    elements.append(Paragraph(f"Number of channels: {nchan}", styles["Normal"]))
    elements.append(Paragraph(f"Channels: {', '.join(ch_names[:10])}...", styles["Normal"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Extracted Features:", styles["Heading2"]))
    for k, v in features.items():
        elements.append(Paragraph(f"{k}: {v:.4f}", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# -------------------
# Streamlit UI
# -------------------
st.title("🧠 EEG-based Depression Detection App")

uploaded_file = st.file_uploader("Upload an EEG file (.edf)", type=["edf"])

if uploaded_file is not None:
    raw = mne.io.read_raw_edf(uploaded_file, preload=False, verbose=False)

    # Show EEG info
    st.subheader("EEG File Info")
    st.info(f"Sampling rate (Hz): {raw.info['sfreq']}")
    st.info(f"Number of channels: {raw.info['nchan']}")
    st.caption(f"Channels: {', '.join(raw.ch_names[:16])}{' ...' if len(raw.ch_names)>16 else ''}")

    # Extract features & Predict
    features = extract_features(raw)
    result, score = predict_depression(features)

    st.subheader("Prediction Result")
    st.success(f"Prediction: {result} (score={score:.2f})")

    # JSON output
    json_result = {
        "prediction": result,
        "score": score,
        "sampling_rate": raw.info["sfreq"],
        "channels": raw.ch_names,
        "features": features,
    }
    st.download_button(
        label="⬇️ Download JSON",
        data=json.dumps(json_result, indent=4),
        file_name="depression_result.json",
        mime="application/json",
    )

    # PDF output
    pdf_buffer = generate_pdf_report(
        result, score, features, raw.info["sfreq"], raw.info["nchan"], raw.ch_names
    )
    st.download_button(
        label="⬇️ Download PDF Report",
        data=pdf_buffer,
        file_name="depression_report.pdf",
        mime="application/pdf",
    )
