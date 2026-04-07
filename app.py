import streamlit as st
import pdfplumber
import json
import re
from groq import Groq

# ─────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TalentBridge AI — Global Hiring Copilot",
    page_icon="🎯",
    layout="wide"
)

# ─────────────────────────────────────────────────────────
# CLIENT
# ─────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    try:
        return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except:
        st.error("❌ GROQ_API_KEY missing. Add in Settings → Secrets")
        st.stop()

client = get_client()

# ─────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────
def extract_pdf(file):
    with pdfplumber.open(file) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)

def call_groq(prompt, tokens=1500):
    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=tokens,
    )
    return res.choices[0].message.content

def safe_json(text):
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except:
            return None
    return None

def score_color(score):
    return "#22c55e" if score >= 75 else "#f59e0b" if score >= 50 else "#ef4444"

# ─────────────────────────────────────────────────────────
# AI ANALYSIS
# ─────────────────────────────────────────────────────────
def analyze_resume(resume, jd):
    prompt = f"""
You are a senior technical recruiter.
Analyze this resume against the job description.
Return ONLY JSON:
{{
 "match_score": 0-100,
 "skills_score": 0-100,
 "experience_score": 0-100,
 "education_score": 0-100,
 "keywords_score": 0-100,
 "matched_skills": [],
 "missing_skills": [],
 "strengths": [],
 "gaps": [],
 "improvements": [],
 "best_roles": []
}}
Resume:
{resume[:3000]}
Job:
{jd[:1500]}
"""
    return safe_json(call_groq(prompt))

# ─────────────────────────────────────────────────────────
# HERO UI
# ─────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center;padding:30px 0'>
    <h1 style='font-size:3rem;margin-bottom:10px;'>🚀 TalentBridge AI</h1>
    <p style='font-size:1.2rem;color:#6b7280'>
        AI Hiring Copilot for Global Tech Jobs 🌍
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📋 Inputs")

    resume_file = st.file_uploader("Upload Resume (PDF)", type="pdf")
    resume_text_input = st.text_area("Or paste resume")

    jd = st.text_area("Job Description (required)")

    run = st.button("🚀 Analyze")

# ─────────────────────────────────────────────────────────
# LANDING PAGE
# ─────────────────────────────────────────────────────────
if not run:
    st.markdown("### ✨ What this product does")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 🎯 ATS Matching")
        st.caption("See how recruiters evaluate your resume")

    with col2:
        st.markdown("#### 🛠 Skill Gap Analysis")
        st.caption("Identify missing skills instantly")

    with col3:
        st.markdown("#### 🚀 Career Optimization")
        st.caption("Get actionable improvement insights")

    st.stop()

# ─────────────────────────────────────────────────────────
# INPUT VALIDATION
# ─────────────────────────────────────────────────────────
resume_text = ""

if resume_file:
    resume_text = extract_pdf(resume_file)
elif resume_text_input:
    resume_text = resume_text_input

if not resume_text:
    st.warning("Upload or paste resume")
    st.stop()

if not jd:
    st.warning("Paste job description")
    st.stop()

# ─────────────────────────────────────────────────────────
# ANALYSIS
# ─────────────────────────────────────────────────────────
with st.spinner("Analyzing your profile..."):
    data = analyze_resume(resume_text, jd)

if not data:
    st.error("AI response failed")
    st.stop()

# ─────────────────────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────────────────────
score = int(data.get("match_score", 0))

st.markdown("## 🎯 Your Match Score")

st.markdown(f"""
<div style='text-align:center;padding:20px;border-radius:15px;background:#f9fafb'>
    <h1 style='font-size:4rem;color:{score_color(score)}'>{score}%</h1>
    <p style='color:#6b7280'>Recruiter Match Score</p>
</div>
""", unsafe_allow_html=True)

st.progress(score)

# Breakdown
cols = st.columns(4)
keys = ["skills_score", "experience_score", "education_score", "keywords_score"]
labels = ["Skills", "Experience", "Education", "Keywords"]

for col, key, label in zip(cols, keys, labels):
    val = int(data.get(key, 0))
    col.metric(label, f"{val}%")

st.markdown("---")

# Skills & Strengths
col1, col2 = st.columns(2)

with col1:
    st.markdown("### ✅ Strengths")
    for s in data.get("strengths", []):
        st.success(s)

with col2:
    st.markdown("### ❌ Missing Skills")
    for s in data.get("missing_skills", []):
        st.error(s)

# Gaps
st.markdown("### ⚠️ Gaps")
for g in data.get("gaps", []):
    st.write(f"- {g}")

# Improvements
st.markdown("### 🚀 Improvements")
for i in data.get("improvements", []):
    st.write(f"- {i}")

# Roles
st.markdown("### 🎯 Best Roles")
for r in data.get("best_roles", []):
    st.write(f"- {r}")

# Download
st.download_button(
    "📄 Download Report",
    json.dumps(data, indent=2),
    "analysis.json"
)

# Footer
st.markdown("---")
st.caption("Built by Faraz Mubeen | AI Engineer | Open to Opportunities 🌍")
