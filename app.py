import streamlit as st
from fpdf import FPDF
import datetime

# --- App Title ---
st.title("🧠 EEG Depression Detection Demo")

# --- Upload EEG File (Demo) ---
uploaded_file = st.file_uploader("Upload EEG file (.edf)", type=["edf"])

if uploaded_file is not None:
    st.success("✅ EEG file uploaded successfully!")

    # --- Fake Prediction (Demo) ---
    st.subheader("Prediction Result")
    depression_level = "Moderate Depression"
    confidence = 82.5  # just an example
    st.write(f"**Result:** {depression_level}")
    st.write(f"**Confidence:** {confidence}%")

    # --- Generate PDF Report ---
    def generate_pdf():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, "EEG Depression Analysis Report", ln=True, align="C")
        pdf.ln(10)

        # Patient Info (dummy data)
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, f"Patient ID: 12345", ln=True)
        pdf.cell(200, 10, f"Date: {datetime.date.today()}", ln=True)
        pdf.ln(10)

        # Prediction results
        pdf.cell(200, 10, f"Predicted Condition: {depression_level}", ln=True)
        pdf.cell(200, 10, f"Confidence: {confidence}%", ln=True)
        pdf.ln(10)

        # Medical Note
        pdf.multi_cell(0, 10, 
            "Note: This is a demo AI-generated analysis based on EEG data.\n"
            "It is intended for research and demonstration purposes only."
        )

        return pdf.output(dest="S").encode("latin-1")

    # Button to download PDF
    pdf_bytes = generate_pdf()
    st.download_button(
        label="📄 Download PDF Report",
        data=pdf_bytes,
        file_name="EEG_Report.pdf",
        mime="application/pdf"
    )


