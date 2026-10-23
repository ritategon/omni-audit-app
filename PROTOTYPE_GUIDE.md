# OMNI-Audit v2.0 Prototype Guide
**Step-by-Step User & Testing Guide for the Research-Grade Orthographic & Marginalia Normalization Integrity Auditor**

* **Author:** Dr. Rita Tegon (`rita.tegon@usal.es` · ORCID: [0000-0002-1225-1806](https://orcid.org/0000-0002-1225-1806))
* **Project Framework:** OMNI-Audit Digital Humanities Diagnostic Suite
* **Source Code:** [gitlab.com/rita.tegon/omni-audit-app](https://gitlab.com/rita.tegon/omni-audit-app)

---

## 1. Introduction & Application Scope (v2.0 Upgrades)

**OMNI-Audit v2.0** (**O**rthographic & **M**arginalia **N**ormalization **I**ntegrity Auditor) is an open-source, research-grade software application engineered to evaluate digitized manuscript collections, HTR outputs (Transkribus, eScriptorium), and crowdsourced transcription datasets for:

1. **Orthographic Normalization (ONI Metric):** Classifies every altered word as a spelling modernisation (rule-based or probable) or as another change (recognition/transcription error), using historical folding rules ($u/v$, $i/j$, $ſ/s$, $y/i$, thorn, *ye/the*, *&/and*, Roman numerals); a **weighted Levenshtein distance** that discounts historical variants is reported alongside the standard Character Error Rate.
2. **Marginalia & Spatial Layout Erasure (MPR & Content Retention Ratio):** Parses multiple TEI-XML schemas (`<add place="margin">`, `<note place="margin">`, `<seg>`, `<zone type="margin">`) and verifies whether the actual *text content* of marginalia was preserved in output streams.
3. **Statistical Line-Level Diagnostics:** Computes CER mean, median, standard deviation ($\sigma$), min, and max across manuscript lines.
4. **Configurable Multi-Factor Risk Assessment:** Assigns a 4-tier compliance score (**Low / Moderate / High / Critical Risk**) with customized recommendations.

---

## 2. Quick Start & Execution Commands

### Prerequisites
* Python 3.8+. The core engine, command-line tool and desktop GUI use only the Python standard library; the web dashboard additionally requires Streamlit (`pip install -r requirements.txt`).

### Running Unit Tests
Validate engine performance and test coverage using standard unittest:

```bash
python -m unittest test_omni_auditor.py
```

### Basic Command Execution

```bash
python omni_auditor.py \
  --diplomatic sample_data/sample_diplomatic.txt \
  --datafied sample_data/sample_datafied.txt \
  --tei-xml sample_data/sample_archival_tei.xml \
  --output-json omni_audit_report.json \
  --verbose
```

---

## 3. Command Line Arguments Reference

| Flag | Parameter Type | Description |
| :--- | :--- | :--- |
| `--diplomatic` | File Path (`.txt`) | Path to the ground-truth diplomatic transcription (preserving $f/s$, $v/u$, regional variants). |
| `--datafied` | File Path (`.txt`) | Path to the OCR/HTR model output or crowdsourced transcription file being audited. |
| `--modernized` | File Path (`.txt`) | *(Optional)* Path to a fully modernized reference text for exact dual-reference ONI calibration. |
| `--tei-xml` | File Path (`.xml`) | Path to the TEI-XML manuscript export file containing layout and structural markup. |
| `--output-json` | File Path (`.json`) | Path where the structured JSON audit report will be saved. |
| `--verbose` | Flag | Enables verbose logging output during execution. |

---

## 4. Sample JSON Diagnostic Audit Output (v2.0)

*Illustrative example of the report structure; actual values depend on the input files.*

```json
{
  "tool": "OMNI-Audit: Orthographic & Marginalia Normalization Integrity Auditor",
  "version": "2.0.0",
  "metrics": {
    "orthographic_normalization_index_oni": 0.4091,
    "character_error_rate_cer": 0.1517,
    "raw_edit_distance": 27.0,
    "weighted_edit_distance": 16.25,
    "oni_calculation_details": {
      "method": "token_level_normalisation_ratio",
      "orthographic_rule_based": 8,
      "orthographic_probable": 1,
      "other_changes": 13
    }
  },
  "line_statistics": {
    "line_count_evaluated": 3,
    "mean_cer": 0.142,
    "median_cer": 0.138,
    "stdev_cer": 0.021
  },
  "xml_markup_audit": {
    "has_marginalia_in_ground_truth": true,
    "mpr_percentage": 100.0,
    "content_retention_ratio": 100.0,
    "tag_breakdown": {
      "margin_additions": 1,
      "margin_notes": 1,
      "total_deletions": 1,
      "total_abbreviations": 1
    }
  },
  "risk_assessment": {
    "risk_level": "MODERATE RISK / MINOR DRIFT",
    "color_code": "YELLOW",
    "recommendations": [
      "Moderate Orthographic Variation: Minor modernization detected in common vocabulary."
    ]
  }
}
```
