import streamlit as st
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import base64

st.title("EEG Depression & Early Alzheimer’s Risk Prototype")
st.subheader("Prototype for Early Alzheimers risk screening using EEG, questionnaires and cognitive micro-tasks.")

uploaded_file = st.file_uploader("Upload your EEG (.edf) file", type=["edf"])

if uploaded_file:
    st.success("File uploaded successfully ✅")
    
    # --- Dummy Analysis (replace later with real model) ---
    # simulate a result
    result = {
        "Early Risk Index": "Moderate",
        "EEG Biomarker Score": 0.62,
        "Cognitive Performance": "Slightly Below Average"
    }
    
    st.write("### Results")
    st.json(result)
    
    # --- JSON download ---
    json_str = json.dumps(result, indent=4)
    st.download_button("Download JSON", data=json_str, file_name="result.json", mime="application/json")
    
    # --- PDF download ---
    def create_pdf(data_dict):
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 50, "EEG Report - Early Alzheimer’s Risk Screening")
        
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 70, "Prototype for early risk screening using EEG, questionnaires and cognitive micro-tasks")
        
        y = height - 110
        for key, value in data_dict.items():
            c.drawString(50, y, f"{key}: {value}")
            y -= 20
        
        c.showPage()
        c.save()
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
    
    pdf_bytes = create_pdf(result)
    b64_pdf = base64.b64encode(pdf_bytes).decode()
    pdf_link = f'<a href="data:application/pdf;base64,{b64_pdf}" download="report.pdf">📄 Download PDF</a>'
    st.markdown(pdf_link, unsafe_allow_html=True)
