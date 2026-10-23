# OMNI-Audit v2.0: Orthographic & Marginalia Normalization Integrity Application

**Author:** Dr. Rita Tegon (`rita.tegon@usal.es` · ORCID: [0000-0002-1225-1806](https://orcid.org/0000-0002-1225-1806))  
**Status:** Experimental research prototype  

---

## 🚀 Live Web Demo

An interactive web dashboard for running OMNI-Audit directly in your browser is available at:  
👉 **[https://omni-audit-app-bupm7z6bqm9xbhdczf7gzm.streamlit.app/](https://omni-audit-app-bupm7z6bqm9xbhdczf7gzm.streamlit.app/)**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://omni-audit-app-bupm7z6bqm9xbhdczf7gzm.streamlit.app/)

*The demo is hosted on Streamlit Community Cloud and may need a few seconds to wake up after a period of inactivity.*

---

## Overview

**OMNI-Audit v2.0** (**O**rthographic & **M**arginalia **N**ormalization **I**ntegrity Auditor) is an experimental, open-source diagnostic application for evaluating digitised manuscript collections, HTR (Handwritten Text Recognition) outputs and crowdsourced archival transcriptions. It compares a diplomatic transcription with a "datafied" version (and, optionally, a modernised reference and a TEI-XML encoding) to detect:

* **Orthographic normalisation:** silent modernisation of historical spellings (u/v, i/j, long s, y/i, thorn), which can also erase regional and dialectal forms;
* **Marginalia erasure:** loss of marginal and interlinear additions, notes and other non-linear layout features recorded in TEI-XML.

---

## Application Files

* **[omni_auditor.py](omni_auditor.py):** Core diagnostic engine & command-line tool.
* **[test_omni_auditor.py](test_omni_auditor.py):** Automated unit test suite (13 tests).
* **[gui_app.py](gui_app.py):** Native desktop dashboard (Tkinter, no external dependencies) for offline use on sensitive or unpublished manuscripts; no data leaves the local machine.
* **[streamlit_app.py](streamlit_app.py):** Interactive web dashboard (Streamlit) powering the live demo.
* **[PROTOTYPE_GUIDE.md](PROTOTYPE_GUIDE.md):** User & testing guide.
* **[TECHNICAL_REPORT.md](TECHNICAL_REPORT.md):** Metrics, weighted edit distance and TEI parsing specification.
* **[sample_data/](sample_data/):** Test files (`sample_diplomatic.txt`, `sample_datafied.txt`, `sample_archival_tei.xml`).
* **[requirements.txt](requirements.txt):** Dependencies for the Streamlit web dashboard.

---

## Execution Commands

### 1. Run Unit Test Suite
```bash
python -m unittest test_omni_auditor.py
```

### 2. Launch Native Desktop GUI Dashboard
```bash
python gui_app.py
```

### 3. Launch Web Application Dashboard Locally
```bash
pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

### 4. Run Command-Line Tool
```bash
python omni_auditor.py \
  --diplomatic sample_data/sample_diplomatic.txt \
  --datafied sample_data/sample_datafied.txt \
  --tei-xml sample_data/sample_archival_tei.xml \
  --output-json omni_audit_report.json \
  --verbose
```

---

## Development Note

OMNI-Audit is an experimental research prototype. The research problem, metrics design, architecture and validation are the author's own; the code was written with the help of AI coding assistants and reviewed and tested by the author.
