"""
OMNI-Audit Web Application Dashboard (Streamlit)
=================================================
Author: Dr. Rita Tegon (rita.tegon@usal.es)
Project: OMNI-Audit (Orthographic & Marginalia Normalization Integrity Auditor)

An interactive web dashboard for evaluating Archival Normalization,
Marginalia Content Loss, and TEI Markup Integrity in real time.
"""

import os
import json
import streamlit as st
from omni_auditor import OMNIAuditor, TextNormalizer, WeightedEditDistance

# Page Configuration
st.set_page_config(
    page_title="OMNI-Audit v2.0 — Web Dashboard",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #003366; margin-bottom: 0px; }
    .sub-header { font-size: 1.0rem; color: #555555; margin-bottom: 20px; font-style: italic; }
    .metric-card { background-color: #F8F9FA; padding: 15px; border-radius: 8px; border-left: 5px solid #003366; }
    .risk-banner-green { background-color: #D4EDDA; color: #155724; padding: 12px; border-radius: 6px; font-weight: bold; }
    .risk-banner-yellow { background-color: #FFF3CD; color: #856404; padding: 12px; border-radius: 6px; font-weight: bold; }
    .risk-banner-orange { background-color: #FFE8D6; color: #D9480F; padding: 12px; border-radius: 6px; font-weight: bold; }
    .risk-banner-red { background-color: #F8D7DA; color: #721C24; padding: 12px; border-radius: 6px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">📜 OMNI-Audit v2.0 Web Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Orthographic & Marginalia Normalization Integrity Auditor | Digital Humanities Diagnostic Tool</div>', unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.header("📁 Input Selection & Data Upload")

sample_data_dir = os.path.join(os.path.dirname(__file__), "sample_data")
load_sample = st.sidebar.button("⚡ Quick Load Sample Manuscript Data")

dip_text = ""
dat_text = ""
mod_text = ""
xml_file_path = None

if load_sample:
    dip_sample_path = os.path.join(sample_data_dir, "sample_diplomatic.txt")
    dat_sample_path = os.path.join(sample_data_dir, "sample_datafied.txt")
    xml_sample_path = os.path.join(sample_data_dir, "sample_archival_tei.xml")

    if os.path.exists(dip_sample_path):
        with open(dip_sample_path, "r", encoding="utf-8") as f:
            dip_text = f.read()
    if os.path.exists(dat_sample_path):
        with open(dat_sample_path, "r", encoding="utf-8") as f:
            dat_text = f.read()
    if os.path.exists(xml_sample_path):
        xml_file_path = xml_sample_path
    st.sidebar.success("Sample manuscript data loaded!")

# File Uploaders
uploaded_dip = st.sidebar.file_uploader("Upload Diplomatic Baseline (.txt)", type=["txt"])
if uploaded_dip:
    dip_text = uploaded_dip.read().decode("utf-8")

uploaded_dat = st.sidebar.file_uploader("Upload Datafied/HTR Output (.txt)", type=["txt"])
if uploaded_dat:
    dat_text = uploaded_dat.read().decode("utf-8")

uploaded_mod = st.sidebar.file_uploader("Upload Modernized Reference (.txt)", type=["txt"])
if uploaded_mod:
    mod_text = uploaded_mod.read().decode("utf-8")

uploaded_xml = st.sidebar.file_uploader("Upload TEI-XML Export (.xml)", type=["xml"])
if uploaded_xml:
    temp_xml_path = os.path.join(os.path.dirname(__file__), "temp_uploaded_tei.xml")
    with open(temp_xml_path, "wb") as f:
        f.write(uploaded_xml.getbuffer())
    xml_file_path = temp_xml_path

# Text Editors in Main Window
col_dip, col_dat = st.columns(2)
with col_dip:
    dip_text = st.text_area("Diplomatic Baseline Text (Ground Truth):", value=dip_text, height=180)
with col_dat:
    dat_text = st.text_area("Datafied / HTR Output Text (To Audit):", value=dat_text, height=180)

# Run Audit Trigger
run_audit = st.button("▶ Run OMNI-Audit Diagnostic Engine", type="primary", use_container_width=True)

if run_audit or (dip_text and dat_text):
    auditor = OMNIAuditor(dip_text, dat_text, mod_text)
    report = auditor.generate_full_report(tei_file_path=xml_file_path)

    # --- Top Metric Cards ---
    col1, col2, col3, col4 = st.columns(4)

    oni = report["metrics"]["orthographic_normalization_index_oni"]
    cer = report["metrics"]["character_error_rate_cer"]
    raw_dist = report["metrics"]["raw_edit_distance"]
    xml_audit = report.get("xml_markup_audit", {})
    mpr = xml_audit.get("mpr_percentage", 100.0)

    with col1:
        st.metric("ONI Score (Normalization)", f"{oni:.4f}", delta="Low Normalization" if oni < 0.2 else "High Normalization", delta_color="inverse")
    with col2:
        st.metric("CER (Character Error Rate)", f"{cer*100:.2f}%", delta=f"{raw_dist:.0f} Edit Distance")
    with col3:
        st.metric("MPR (Marginalia Ratio)", f"{mpr:.1f}%", delta="Layout Intact" if mpr >= 90 else "Layout Loss")
    with col4:
        content_ret = xml_audit.get("content_retention_ratio", 100.0)
        st.metric("Content Retention", f"{content_ret:.1f}%")

    # --- Risk Assessment Banner ---
    risk = report["risk_assessment"]
    level_name = risk["risk_level"]
    color_code = risk["color_code"]

    st.subheader("Diagnostic Risk Evaluation")
    if color_code == "GREEN":
        st.markdown(f'<div class="risk-banner-green">✅ STATUS: {level_name}</div>', unsafe_allow_html=True)
    elif color_code == "YELLOW":
        st.markdown(f'<div class="risk-banner-yellow">⚠️ STATUS: {level_name}</div>', unsafe_allow_html=True)
    elif color_code == "ORANGE":
        st.markdown(f'<div class="risk-banner-orange">🍊 STATUS: {level_name}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="risk-banner-red">🚨 STATUS: {level_name}</div>', unsafe_allow_html=True)

    # Recommendations
    st.write("**Actionable Recommendations:**")
    for rec in risk["recommendations"]:
        st.info(f"👉 {rec}")

    # Tabs for Detailed Diagnostics
    tab_report, tab_xml, tab_lines = st.tabs(["📊 Full JSON Report", "🏛️ TEI-XML Markup Audit", "📏 Line Statistics"])

    with tab_report:
        report_json_str = json.dumps(report, indent=2, ensure_ascii=False)
        st.json(report)
        st.download_button("💾 Download Audit Report (JSON)", data=report_json_str, file_name="omni_audit_report.json", mime="application/json")

    with tab_xml:
        if xml_audit:
            st.write("**TEI-P5 Markup Breakdown:**")
            st.write(xml_audit.get("tag_breakdown", {}))
            samples = xml_audit.get("extracted_marginalia_samples", [])
            if samples:
                st.write("**Extracted Marginalia Samples:**")
                for s in samples:
                    st.code(s)
        else:
            st.warning("No TEI-XML file provided for layout analysis.")

    with tab_lines:
        line_stats = report.get("line_statistics", {})
        st.write(line_stats)
else:
    st.info("👈 Please enter text or click 'Quick Load Sample Manuscript Data' in the sidebar to start auditing.")
