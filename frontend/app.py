import streamlit as st
import requests
import PyPDF2
import docx
import pandas as pd
import matplotlib.pyplot as plt
import re

API_URL = "http://127.0.0.1:8000/analyze"

st.set_page_config(page_title="AI Research Analyst", layout="wide")

# ---------- STYLING ----------
st.markdown("""
<style>
.main {
    background-color: #0e1117;
    color: white;
}
.block-container {
    padding-top: 2rem;
}
.stButton>button {
    background-color: #4CAF50;
    color: white;
    border-radius: 10px;
    height: 50px;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("🧠 AI Research Analyst")
st.caption("CoWork-style AI system with insights & visual analytics")

# ---------- FILE EXTRACTION ----------
def extract_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_docx(file):
    doc = docx.Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_excel(file):
    df = pd.read_excel(file)
    return df.to_string()

# ---------- CHART GENERATION ----------
def generate_chart(text):
    words = re.findall(r'\w+', text.lower())

    keywords = ["ai", "data", "cost", "privacy", "healthcare"]
    counts = [words.count(k) for k in keywords]

    fig, ax = plt.subplots()
    ax.bar(keywords, counts)
    ax.set_title("Key Concept Frequency")

    return fig

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("⚙️ Settings")
    input_mode = st.radio("Input Type", ["Text", "File"])
    st.markdown("---")
    st.info("Tip: Upload PDFs for deeper analysis")

# ---------- INPUT ----------
text_input = ""

if input_mode == "Text":
    text_input = st.text_area(
        "Paste your research text:",
        height=250,
        placeholder="Paste article, notes, or research here..."
    )

else:
    uploaded_file = st.file_uploader(
        "Upload file",
        type=["pdf", "docx", "xlsx"]
    )

    if uploaded_file:
        if uploaded_file.name.endswith(".pdf"):
            text_input = extract_pdf(uploaded_file)

        elif uploaded_file.name.endswith(".docx"):
            text_input = extract_docx(uploaded_file)

        elif uploaded_file.name.endswith(".xlsx"):
            text_input = extract_excel(uploaded_file)

        st.success("File loaded successfully ✅")

# ---------- ANALYZE ----------
if st.button("🚀 Analyze Now"):

    if not text_input.strip():
        st.warning("Please provide input")
    else:
        with st.spinner("AI agents working..."):

            try:
                response = requests.post(
                    API_URL,
                    json={"text": text_input}
                )

                if response.status_code == 200:
                    data = response.json()

                    st.success("Analysis Complete ✅")

                    # Tabs
                    tab1, tab2, tab3, tab4 = st.tabs(
                        ["🧠 Plan", "🔬 Analysis", "💡 Insights", "📊 Charts"]
                    )

                    with tab1:
                        st.write(data["plan"])

                    with tab2:
                        st.write(data["analysis"])

                    with tab3:
                        st.write(data["insights"])

                    with tab4:
                        st.subheader("📊 Visualization")
                        fig = generate_chart(data["analysis"])
                        st.pyplot(fig)

                else:
                    st.error("Backend error")

            except Exception as e:
                st.error(f"Error: {str(e)}")