"""
JD Analysis Page
Displays comprehensive AI-powered job description analysis
"""

import streamlit as st
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

st.set_page_config(
    page_title="JD Analysis - ATS Forge",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 AI Job Description Analysis")

# Check if JD analysis exists in session state
if 'jd_analysis' not in st.session_state or not st.session_state.jd_analysis:
    st.warning("⚠️ No JD analysis available")
    st.info("👈 Go to the main page and run an analysis first")
    st.stop()

jd_ai = st.session_state.jd_analysis

# Job Summary Card
st.header("📝 What This Company Wants")
st.info(jd_ai.get('job_summary', 'Analysis unavailable'))

# Company Expectations
if jd_ai.get('company_expectations'):
    st.header("🎯 Post-Hire Expectations")
    st.success(jd_ai.get('company_expectations'))

st.divider()

# Key Metrics
st.header("📊 Key Job Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Job Type", jd_ai.get('job_type', 'Not specified'))
with col2:
    st.metric("Seniority", jd_ai.get('seniority_level', 'Not specified'))
with col3:
    st.metric("Experience", jd_ai.get('experience_required', 'Not specified'))
with col4:
    st.metric("Education", jd_ai.get('education_required', 'Not specified'))

st.divider()

# Responsibilities
if jd_ai.get('key_responsibilities'):
    st.header("💼 Key Responsibilities")
    for resp in jd_ai['key_responsibilities']:
        st.markdown(f"• {resp}")
    st.divider()

# Required Skills
st.header("✅ Required Skills")
req_skills = jd_ai.get('required_skills', {})

col1, col2 = st.columns(2)
with col1:
    st.subheader("💻 Technical Skills")
    tech_skills = req_skills.get('technical', [])
    if tech_skills:
        for skill in tech_skills[:15]:
            st.markdown(f"• {skill}")
    else:
        st.caption("None specified")

with col2:
    st.subheader("🤝 Soft Skills")
    soft_skills = req_skills.get('soft', [])
    if soft_skills:
        for skill in soft_skills[:10]:
            st.markdown(f"• {skill}")
    else:
        st.caption("None specified")

st.divider()

# Preferred Skills
pref_skills = jd_ai.get('preferred_skills', {})
if pref_skills.get('technical') or pref_skills.get('soft'):
    st.header("⭐ Preferred Skills (Nice to Have)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💻 Technical")
        pref_tech = pref_skills.get('technical', [])
        if pref_tech:
            for skill in pref_tech[:10]:
                st.markdown(f"• {skill}")
        else:
            st.caption("None specified")
    
    with col2:
        st.subheader("🤝 Soft Skills")
        pref_soft = pref_skills.get('soft', [])
        if pref_soft:
            for skill in pref_soft[:10]:
                st.markdown(f"• {skill}")
        else:
            st.caption("None specified")

st.divider()

# Qualifications
if jd_ai.get('required_qualifications'):
    st.header("🎓 Required Qualifications")
    for qual in jd_ai['required_qualifications']:
        st.markdown(f"• {qual}")

if jd_ai.get('preferred_qualifications'):
    st.header("⭐ Preferred Qualifications")
    for qual in jd_ai['preferred_qualifications']:
        st.markdown(f"• {qual}")
