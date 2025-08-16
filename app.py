import streamlit as st
import numpy as np
from fpdf import FPDF
import os

# =========================
# Function to generate PDF
# =========================
def generate_report(patient_name, result, probability):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Depression Detection Report", ln=True, align='C')

    pdf.set_font("Arial", size=12)
    pdf.ln(10)

    pdf.cell(200, 10, txt=f"Patient Name: {patient_name}", ln=True)
    pdf.cell(200, 10, txt=f"Diagnosis Result: {result}", ln=True)
    pdf.cell(200, 10, txt=f"Model Confidence: {probability:.2f}%", ln=True)

    pdf.ln(10)
    pdf.multi_cell(0, 10, txt=(
        "This report was generated using AI analysis of EEG signals.\n"
        "Note: This is a decision-support tool and not a substitute for "
        "professional medical diagnosis."
    ))

    filename = f"report_{patient_name.replace(' ', '_')}.pdf"
    pdf.output(filename)
    return filename

# =========================
# Streamlit App
# =========================
st.title("🧠 EEG Depression Detection App")
st.write("Upload EEG data and generate a diagnostic report.")

# Example UI
patient_name = st.text_input("Enter Patient Name:")

if st.button("Run Analysis"):
    # Fake model result (for demo) → replace with your ML prediction
    result = "Depression Detected"
    probability = np.random.uniform(70, 95)  # simulated confidence
    
    st.success(f"**Result:** {result} (Confidence: {probability:.2f}%)")

    # Generate PDF
    pdf_file = generate_report(patient_name, result, probability)

    # Allow download
    with open(pdf_file, "rb") as f:
        st.download_button(
            label="📥 Download PDF Report",
            data=f,
            file_name=pdf_file,
            mime="application/pdf"
        )


