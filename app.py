import streamlit as st
import mne
import numpy as np
import json
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# ثبت فونت عربی/فارسی (Amiri)
pdfmetrics.registerFont(TTFont("Amiri", "/usr/share/fonts/truetype/amiri/Amiri-Regular.ttf"))

# عنوان اصلی
st.title("🧠 EEG Depression & Alzheimer’s Early Risk App")

# زیرعنوان علمی
st.markdown(
    "<h5 style='color:gray;'>Prototype for early Alzheimer’s risk screening using EEG, questionnaires and cognitive micro-tasks.</h5>",
    unsafe_allow_html=True
)

# آپلود فایل EEG (.edf)
uploaded_file = st.file_uploader("📂 لطفاً فایل EEG با فرمت .edf را آپلود کنید", type=["edf"])

if uploaded_file is not None:
    # بارگذاری EEG
    raw = mne.io.read_raw_edf(uploaded_file, preload=True, verbose=False)
    data, times = raw[:, :1000]  # نمونه داده (۱۰۰۰ تایم‌پوینت اول)
    mean_signal = np.mean(data)

    # 🔹 شبیه‌سازی پیش‌بینی مدل
    if mean_signal > 0:
        prediction = "Mild Depression"
        early_risk_index = 0.35
    else:
        prediction = "Severe Depression"
        early_risk_index = 0.72

    st.success(f"✅ Prediction: {prediction}")
    st.info(f"🧾 Early Risk Index: {early_risk_index:.2f}")

    # =====================
    # 📄 ساخت گزارش PDF
    # =====================
    def create_pdf(prediction, early_risk_index):
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        c.setFont("Amiri", 14)
        c.drawString(100, 800, "EEG Depression & Alzheimer’s Risk Report")
        c.drawString(100, 770, f"Prediction: {prediction}")
        c.drawString(100, 750, f"Early Risk Index: {early_risk_index:.2f}")
        c.drawString(100, 720, "مرحباً بكم، هذا التقرير يوضح نتيجة تحليل EEG للفحص المبكر عن الاكتئاب و خطر الزهايمر.")
        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer

    pdf_file = create_pdf(prediction, early_risk_index)

    # =====================
    # 📦 ساخت گزارش JSON
    # =====================
    def create_json(prediction, early_risk_index):
        report = {
            "prediction": prediction,
            "early_risk_index": early_risk_index,
            "note": "Prototype result for early Alzheimer’s risk screening"
        }
        return json.dumps(report, indent=4).encode("utf-8")

    json_file = create_json(prediction, early_risk_index)

    # =====================
    # 📥 دکمه‌های دانلود
    # =====================
    st.download_button(
        label="⬇️ Download PDF Report",
        data=pdf_file,
        file_name="report.pdf",
        mime="application/pdf"
    )

    st.download_button(
        label="⬇️ Download JSON Report",
        data=json_file,
        file_name="report.json",
        mime="application/json"
    )
