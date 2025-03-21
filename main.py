import streamlit as st
import openai
import os
from PyPDF2 import PdfReader
from pydantic import BaseModel, Field
from typing import List
import json
import re

# --- Streamlit setup ---
st.set_page_config(page_title="Contract AI Reviewer | Reactiiv Media", layout="wide")

# --- Branding ---
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.title("📜 Contract AI Reviewer")
    st.markdown("##### Powered by Reactiiv Media")
with col2:
    st.image("logo.png", width=120)  # Replace with actual logo

st.markdown("---")

# --- Sidebar API Key Management ---
st.sidebar.image("logo.png", use_container_width=True)  # Replace with actual logo
st.sidebar.header("🔐 OpenAI API Configuration")
if 'openai_api_key' not in st.session_state:
    st.session_state['openai_api_key'] = ''
api_key_input = st.sidebar.text_input('Enter your OpenAI API Key', type='password')
if st.sidebar.button('Save API Key'):
    st.session_state['openai_api_key'] = api_key_input
    st.sidebar.success('API Key saved!')

# --- Pydantic models ---
class ContractAnalysis(BaseModel):
    parties: List[str] = Field(description="Parties involved")
    deadlines: List[str] = Field(description="Important deadlines")
    payment_terms: str = Field(description="Payment terms summary")
    renewal_dates: List[str] = Field(description="Renewal dates")
    risk_clauses: List[str] = Field(description="Critical risk clauses")
    missing_unfavorable_clauses: List[str] = Field(description="Missing or unfavorable clauses")
    recommendations: List[str] = Field(description="Recommended areas for manual review")

# --- Helper functions ---
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def analyze_contract(text, api_key):
    openai.api_key = api_key

    system_prompt = """You are an expert legal contract analyzer. Provide clear, concise summaries and highlight key risks and missing clauses in contracts."""

    user_prompt = f"""
    Analyze the following contract and summarize clearly:
    
    {text}
    
    Provide the results strictly in JSON format:
    {{
      "parties": ["party1", "party2"],
      "deadlines": ["date1", "date2"],
      "payment_terms": "summary of payment terms",
      "renewal_dates": ["renewal date1", "renewal date2"],
      "risk_clauses": ["risk clause1", "risk clause2"],
      "missing_unfavorable_clauses": ["clause1", "clause2"],
      "recommendations": ["recommendation1", "recommendation2"]
    }}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        max_tokens=1500
    )

    json_response = response.choices[0].message.content.strip()
    json_response = re.sub(r"```(?:json)?\s*|\s*```", "", json_response, flags=re.DOTALL).strip()

    try:
        parsed_json = json.loads(json_response)
        return ContractAnalysis(**parsed_json)
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse JSON: {e}\nRaw response:\n{json_response}")
        raise ValueError(f"Invalid JSON response: {e}") from e

# --- File Upload and Analysis Section ---
st.markdown("### 📂 Upload Your Contract Files (PDF)")
st.markdown("Upload one or more contracts, and our AI will analyze them for key information.")
uploaded_files = st.file_uploader("Upload Contracts", type=['pdf'], accept_multiple_files=True)

if uploaded_files and st.button("🔍 Analyze Contracts"):
    if not st.session_state['openai_api_key']:
        st.error("❌ Please enter and save your OpenAI API key in the sidebar.")
    else:
        for file in uploaded_files:
            with st.expander(f"📑 Contract Analysis: {file.name}"):
                contract_text = extract_text_from_pdf(file)
                analysis_result = analyze_contract(contract_text, st.session_state['openai_api_key'])

                st.markdown("### 📋 Summary Report")
                
                def display_field(title, value):
                    if isinstance(value, list):
                        if not value:
                            st.markdown(f"**{title}:** N/A")
                        else:
                            st.markdown(f"**{title}:**")
                            for item in value:
                                st.markdown(f"- {item}")
                    else:
                        if not value or value.strip().lower() == "n/a":
                            st.markdown(f"**{title}:** N/A")
                        else:
                            st.markdown(f"**{title}:** {value}")
                
                display_field("👥 Parties Involved", analysis_result.parties)
                display_field("📅 Deadlines", analysis_result.deadlines)
                display_field("💰 Payment Terms", analysis_result.payment_terms)
                display_field("🔄 Renewal Dates", analysis_result.renewal_dates)
                display_field("⚠️ Critical Risk Clauses", analysis_result.risk_clauses)
                display_field("🚨 Missing or Unfavorable Clauses", analysis_result.missing_unfavorable_clauses)
                display_field("📝 Recommendations for Manual Review", analysis_result.recommendations)
                
                st.markdown("---")

# --- Footer ---
st.markdown("---")
st.markdown("📢 **Reactiv Media | AI-Powered Contract Analysis**")
st.markdown("📧 Contact us: support@reactiivmedia.com")