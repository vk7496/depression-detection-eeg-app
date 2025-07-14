
import streamlit as st
import mne
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import zipfile

def extract_bandpower(data, sf, band, window_sec=None):
    from scipy.signal import welch
    band = np.array(band)
    low, high = band

    if window_sec is not None:
        nperseg = int(window_sec * sf)
    else:
        nperseg = (2 / low) * sf

    freqs, psd = welch(data, sf, nperseg=nperseg)
    freq_res = freqs[1] - freqs[0]
    idx_band = np.logical_and(freqs >= low, freqs <= high)
    band_power = np.sum(psd[idx_band]) * freq_res
    return band_power

st.set_page_config(page_title="EEG Depression Detector", layout="wide")
st.title("🧠 EEG-Based Depression Detection Demo")

uploaded_file = st.file_uploader("Upload an EDF file", type="edf")

    if uploaded_file is not None:
    st.success("File uploaded successfully!")
    # ذخیره فایل موقت روی دیسک
    with open("temp.edf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    # خواندن فایل ذخیره‌شده با mne
    raw = mne.io.read_raw_edf("temp.edf", preload=True, verbose=False)

    # فیلتر کردن سیگنال EEG
    raw.filter(1., 50., fir_design='firwin', verbose=False)

    # استخراج دیتا و زمان از یک کانال
    data, times = raw[:1, :]
        
    # نمایش سیگنال EEG
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(times, data[0], color='purple')
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("EEG signal (uV)")
    ax.set_title("Raw EEG Signal")
    st.pyplot(fig)

    sf = raw.info['sfreq']

    # استخراج ویژگی‌ها
    features = {
        'delta': extract_bandpower(data[0], sf, [0.5, 4]),
        'theta': extract_bandpower(data[0], sf, [4, 8]),
        'alpha': extract_bandpower(data[0], sf, [8, 13]),
        'beta': extract_bandpower(data[0], sf, [13, 30]),
        'gamma': extract_bandpower(data[0], sf, [30, 45]),
    }

    st.subheader("🧬 Extracted Features")
    st.json(features)

    # تشخیص اولیه افسردگی (صرفاً برای نسخه دمو)
    prediction = "Depressed" if features['theta'] > features['alpha'] else "Not Depressed"
    st.subheader("📢 AI Prediction:")
    st.success(f"The model predicts: **{prediction}**")
else:
    st.info("Please upload an EDF file to begin.")
