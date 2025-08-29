import streamlit as st
import numpy as np
import mne
import os

# --------------------------
# عنوان برنامه
# --------------------------
st.set_page_config(page_title="EEG Depression & Cognitive Assessment", layout="centered")

st.title("🧠 EEG-based Depression & Cognitive Assessment (Demo)")
st.write("Prototype demo combining EEG, Questionnaire, and Cognitive Test.")

# --------------------------
# آپلود EEG
# --------------------------
st.header("📤 EEG Data Upload")

uploaded_file = st.file_uploader("Upload your EEG file (.edf)", type=["edf"])

if uploaded_file is not None:
    try:
        # ذخیره موقت فایل آپلودی
        temp_filename = "temp_eeg.edf"
        with open(temp_filename, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # خواندن فایل EEG با MNE
        raw = mne.io.read_raw_edf(temp_filename, preload=True, verbose=False)

        # استخراج سیگنال
        data, times = raw[:]
        eeg_mean = np.mean(data)

        # محاسبه یک امتیاز نمایشی (Demo)
        depression_score = int(abs(eeg_mean) * 100) % 100
        st.success(f"✅ EEG file uploaded successfully! Depression Risk Score: **{depression_score}/100**")

        # حذف فایل موقت
        os.remove(temp_filename)

    except Exception as e:
        st.error(f"⚠️ Error while processing EEG file: {e}")

# --------------------------
# پرسشنامه ساده خلق و خواب
# --------------------------
st.header("📝 Mood & Sleep Questionnaire")
q1 = st.radio("Over the last 2 weeks, how often have you felt little interest or pleasure in doing things?",
              ["Not at all", "Several days", "More than half the days", "Nearly every day"])
q2 = st.radio("Over the last 2 weeks, how often have you had trouble falling or staying asleep?",
              ["Not at all", "Several days", "More than half the days", "Nearly every day"])

if q1 or q2:
    st.write("✅ Responses recorded.")

# --------------------------
# توضیح پروژه
# --------------------------
st.header("ℹ️ About this Project")
st.markdown("""
This project is a **prototype web app** built with [Streamlit](https://streamlit.io/) that combines:

- EEG data analysis  
- Mood & sleep questionnaires  
- Cognitive assessment demo  

⚠️ *Note: This is a prototype and not a medical diagnostic tool.*
""")
