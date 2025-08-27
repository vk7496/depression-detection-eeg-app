import streamlit as st
import random
import json
from datetime import datetime

# ------------------------
# Title
# ------------------------
st.set_page_config(page_title="Depression Assessment Demo", layout="centered")
st.title("🧠 Depression & Cognitive Assessment (Demo)")
st.write("Prototype demo combining **EEG**, **Questionnaire**, and **Cognitive Test**.")

# ------------------------
# Section 1: EEG Upload
# ------------------------
st.header("📂 EEG Data Upload")
uploaded_eeg = st.file_uploader("Upload your EEG file (.edf)", type=["edf"])

if uploaded_eeg is not None:
    st.success("EEG file uploaded successfully ✅")
    eeg_score = random.randint(30, 80)  # Simulated analysis
    st.write(f"**EEG Depression Risk Score:** {eeg_score}/100")
else:
    eeg_score = None

# ------------------------
# Section 2: Questionnaire
# ------------------------
st.header("📝 Mood & Sleep Questionnaire")
q1 = st.slider("Over the last 2 weeks, how often have you felt little interest or pleasure in doing things?", 0, 3, 1)
q2 = st.slider("How often have you felt down, depressed, or hopeless?", 0, 3, 1)
q3 = st.slider("How would you rate your sleep quality?", 1, 5, 3)

questionnaire_score = q1 + q2 + (6 - q3)  # higher = worse mood/sleep
st.write(f"**Questionnaire Score:** {questionnaire_score}")

# ------------------------
# Section 3: Cognitive Test (Working Memory)
# ------------------------
st.header("🧩 Cognitive Test (n-back)")
st.write("Press the button if the current number matches the one shown 2 steps earlier.")

if "sequence" not in st.session_state:
    st.session_state.sequence = []
    st.session_state.correct = 0
    st.session_state.shown = 0

if st.button("Show Next Number"):
    num = random.randint(1, 9)
    st.session_state.sequence.append(num)
    st.session_state.shown += 1
    st.write(f"### {num}")

if st.button("Match!"):
    if len(st.session_state.sequence) >= 3:
        if st.session_state.sequence[-1] == st.session_state.sequence[-3]:
            st.session_state.correct += 1
            st.success("Correct ✅")
        else:
            st.error("Wrong ❌")
    else:
        st.warning("Not enough numbers yet.")

st.write(f"**Correct Responses:** {st.session_state.correct}")

# ------------------------
# Section 4: Combined Index
# ------------------------
st.header("📊 Combined Assessment Index")

if eeg_score is not None:
    combined = (eeg_score * 0.5) + (questionnaire_score * 10 * 0.3) + (st.session_state.correct * 5 * 0.2)
    combined = min(100, int(combined))
    st.metric("Final Combined Score", f"{combined}/100")

    if combined < 40:
        st.success("🟢 Low Risk of Depression")
    elif combined < 70:
        st.warning("🟡 Moderate Risk of Depression")
    else:
        st.error("🔴 High Risk of Depression")

    # ------------------------
    # Save Report as JSON
    # ------------------------
    report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "EEG_score": eeg_score,
        "Questionnaire_score": questionnaire_score,
        "Cognitive_correct": st.session_state.correct,
        "Combined_index": combined
    }

    st.download_button(
        label="📥 Download Report (JSON)",
        data=json.dumps(report, indent=4),
        file_name="depression_report.json",
        mime="application/json"
    )
else:
    st.info("Please upload an EEG file to calculate the final index.")



