import streamlit as st
import numpy as np
import mne

# -----------------------------
# Title & Description
# -----------------------------
st.title("🧠 Depression & Cognitive Assessment (Demo)")
st.write("Prototype for early Alzheimer’s risk screening using EEG, questionnaires, and cognitive micro-tasks.")

# -----------------------------
# EEG Upload & Processing
# -----------------------------
st.header("📊 EEG Data Upload")

uploaded_file = st.file_uploader("Upload your EEG file (.edf)", type=["edf"])

if uploaded_file is not None:
    st.success("EEG file uploaded successfully ✅")

    # Load EEG data (demo only, using mne for .edf)
    try:
        raw = mne.io.read_raw_edf(uploaded_file, preload=True, verbose=False)
        data, times = raw[:]
        # Simple feature extraction: mean power (demo only)
        eeg_feature = np.mean(np.abs(data))
        eeg_score = int(min(100, eeg_feature % 100)) # normalize to 0-100
    except Exception as e:
        st.error(f"Error reading EEG file: {e}")
        eeg_score = None

    if eeg_score is not None:
        st.write(f"🧾 Early Risk Index (EEG-based): {eeg_score}/100")

else:
    eeg_score = None

# -----------------------------
# Questionnaire Section
# -----------------------------
st.header("📝 Mood & Sleep Questionnaire")

q1 = st.radio("Over the last 2 weeks, how often have you felt little interest or pleasure in doing things?",
              ["Not at all", "Several days", "More than half the days", "Nearly every day"])

q2 = st.radio("Over the last 2 weeks, how often have you had trouble falling or staying asleep?",
              ["Not at all", "Several days", "More than half the days", "Nearly every day"])

# Map answers to scores
answer_map = {
    "Not at all": 0,
    "Several days": 1,
    "More than half the days": 2,
    "Nearly every day": 3
}
questionnaire_score = (answer_map[q1] + answer_map[q2]) * 10 # scale to 0-60
questionnaire_score = int(min(100, questionnaire_score))

st.write(f"📋 Questionnaire Risk Score: {questionnaire_score}/100")

# -----------------------------
# Simple Cognitive Test
# -----------------------------
st.header("🧠 Cognitive Micro-Test")

st.write("Memory test: Remember the sequence **3 - 7 - 4**. Now select the correct sequence:")

cog_answer = st.selectbox("Which is correct?", ["3 - 7 - 4", "4 - 7 - 3", "7 - 3 - 4"])

if cog_answer == "3 - 7 - 4":
    cog_score = 90
else:
    cog_score = 40

st.write(f"🧠 Cognitive Performance Score: {cog_score}/100")

# -----------------------------
# Final Index
# -----------------------------
if eeg_score is not None:
    final_index = (0.5 * eeg_score) + (0.2 * questionnaire_score) + (0.3 * cog_score)
    st.success(f"🌟 Final Early Alzheimer’s Risk Index: {final_index:.1f}/100")
else:
    st.info("Upload EEG file to calculate the final index.")
