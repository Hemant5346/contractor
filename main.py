import streamlit as st
import openai
from PyPDF2 import PdfReader
from pydantic import BaseModel, Field
from typing import List
import json
import re

# --- Page Setup ---
st.set_page_config(page_title="Contract AI Reviewer", layout="wide", page_icon="📑")

# --- Custom CSS ---
st.markdown("""
<style>
    .main-title {
        font-size: 50px;
        font-weight: 700;
        color: #FFFFFF;
        background-color: #4A90E2;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
    }
    .subheader {
        font-size: 20px;
        font-weight: 600;
        color: #4A90E2;
        margin-top: 20px;
    }
    .report-box {
        border-radius: 10px;
        padding: 15px;
        background-color: #F2F6FF;
        margin-bottom: 20px;
    }
    .sidebar .stButton>button {
        background-color: #4A90E2;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("<div class='main-title'>Reactiiv Media - Contract AI Reviewer 📑</div>", unsafe_allow_html=True)

# --- API Key Management ---
if 'openai_api_key' not in st.session_state:
    st.session_state['openai_api_key'] = ''

with st.sidebar:
    st.header('⚙️ OpenAI API Configuration')
    api_key_input = st.text_input('🔑 OpenAI API Key', type='password')
    if st.button('Save API Key'):
        st.session_state['openai_api_key'] = api_key_input
        st.success('✅ API Key saved successfully!')

# --- Pydantic Model ---
class ContractAnalysis(BaseModel):
    parties: List[str]
    deadlines: List[str]
    payment_terms: str
    renewal_dates: List[str]
    risk_clauses: List[str]
    missing_unfavorable_clauses: List[str]
    recommendations: List[str]

# --- Helper Functions ---
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    return " ".join(page.extract_text() for page in reader.pages)

def analyze_contract(text, api_key):
    openai.api_key = api_key

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": "You are an expert legal contract analyzer."},
            {"role": "user", "content": f"Analyze contract:\n{text}\nProvide JSON output."}
        ],
        temperature=0.2,
        max_tokens=1500
    )

    json_response = re.sub(r"```(?:json)?\s*|\s*```", "", response.choices[0].message.content.strip(), flags=re.DOTALL)
    return ContractAnalysis(**json.loads(json_response))

# --- File Upload ---
uploaded_files = st.file_uploader('📂 Upload Contract Files (PDF)', type=['pdf'], accept_multiple_files=True)

if uploaded_files and st.button("🚀 Analyze Contracts"):
    if not st.session_state['openai_api_key']:
        st.error("❗ Please enter and save your OpenAI API key in the sidebar.")
    else:
        for file in uploaded_files:
            with st.expander(f"📄 Contract Analysis: {file.name}"):
                contract_text = extract_text_from_pdf(file)
                try:
                    analysis_result = analyze_contract(contract_text, st.session_state['openai_api_key'])
                except Exception as e:
                    st.error(f"⚠️ Analysis failed: {e}")
                    continue

                st.markdown("<div class='subheader'>📋 Summary Report</div>", unsafe_allow_html=True)

                def display_field(title, content):
                    if not content:
                        content = ["N/A"] if isinstance(content, list) else "N/A"
                    if isinstance(content, list):
                        content = "<br>".join(f"• {item}" for item in content)
                    st.markdown(f"<div class='report-box'><b>{title}:</b><br>{content}</div>", unsafe_allow_html=True)

                display_field("Parties Involved", analysis_result.parties)
                display_field("Deadlines", analysis_result.deadlines)
                display_field("Payment Terms", analysis_result.payment_terms)
                display_field("Renewal Dates", analysis_result.renewal_dates)
                display_field("Critical Risk Clauses", analysis_result.risk_clauses)
                display_field("Missing/Unfavorable Clauses", analysis_result.missing_unfavorable_clauses)
                display_field("Recommendations", analysis_result.recommendations)

                st.markdown("---")