import streamlit as st
import mne
import os

st.set_page_config(page_title="EEG Depression Detection Demo", page_icon="🧠")

st.title("🧠 EEG-Based Depression Detection Demo")

uploaded_file = st.file_uploader("Upload an EDF file", type=["edf"])

if uploaded_file is not None:
    st.success("File uploaded successfully!")

    # ذخیره فایل آپلودی به صورت موقت
    with open("temp_file.edf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    # خواندن فایل با MNE
    raw = mne.io.read_raw_edf("temp_file.edf", preload=True, verbose=False)
    raw.filter(1., 50., fir_design='firwin', verbose=False)

    # استخراج داده و زمان
    data, times = raw[:1, :]  # یک کانال نمونه
    st.write("Sampling frequency:", raw.info['sfreq'])
    st.write("Data shape:", data.shape)

