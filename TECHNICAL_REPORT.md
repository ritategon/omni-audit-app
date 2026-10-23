# OMNI-Audit v2.0 Technical Report & Specification
**Mathematical Foundations, Weighted Distance Matrices, and TEI Parsing Architecture**

* **Author:** Dr. Rita Tegon (`rita.tegon@usal.es` · ORCID: [0000-0002-1225-1806](https://orcid.org/0000-0002-1225-1806))  
* **Project Framework:** OMNI-Audit Digital Humanities Diagnostic Suite  
* **Source Code:** [gitlab.com/rita.tegon/omni-audit-app](https://gitlab.com/rita.tegon/omni-audit-app)

---

## 1. Executive Summary & Research Methodology

When historical manuscripts are converted into digital data via neural Handwritten Text Recognition (HTR) models or crowdsourced volunteer transcription, they undergo **silent normalization**. Neural language models trained on standard modern corpora systematically alter archaic spelling ($u/v$, $i/j$, $ſ/s$, scribal suspensions) to modern standards, while user interfaces often collapse non-linear marginalia, strikethroughs, and interlinear additions.

**OMNI-Audit v2.0** provides a mathematically rigorous, research-grade software engine designed to isolate and quantify these phenomena without false-positive inflation.

---

## 2. Mathematical & Algorithmic Foundations (v2.0)

### A. Weighted Levenshtein Edit Distance Matrix
To avoid treating historical orthographic variants (e.g., $u \leftrightarrow v$) with the same penalty as arbitrary character loss/noise, OMNI-Audit implements a weighted substitution matrix:

$$Cost(c_1, c_2) = \begin{cases} 
0.0 & \text{if } c_1 = c_2 \\
0.10 & \text{if case difference only } (C \leftrightarrow c) \\
0.25 & \text{if historical variant } (u \leftrightarrow v, i \leftrightarrow j, ſ \leftrightarrow s, \text{brevigraphs}) \\
1.00 & \text{if arbitrary substitution / noise}
\end{cases}$$

### B. Self-Calibrated Orthographic Normalization Index ($\text{ONI}$)
Rather than assuming a modernized text is the upper limit of error, OMNI-Audit computes $\text{ONI}$ by isolating orthographic variance:

$$\text{ONI} = \frac{D_{\text{unweighted}}(T_{\text{dip}}, T_{\text{dat}}) - D_{\text{weighted}}(T_{\text{dip}}, T_{\text{dat}})}{\max(D_{\text{unweighted}}(T_{\text{dip}}, T_{\text{dat}}), 1.0)}$$

* **Interpretation:**
  * $\text{ONI} = 0.0$: All character edits represent random OCR noise or identical matching.
  * $\text{ONI} > 0.40$: High proportion of character edits are specifically modernizing orthographic conversions.

### C. Marginalia Preservation & Content Retention Ratio ($\text{MPR}$)
The parser evaluates both tag retention and textual content presence across multiple TEI-P5 elements (`<add place="margin|left|right|above">`, `<note place="margin">`, `<zone type="margin">`):

$$\text{MPR} = \left( \frac{N_{\text{captured\_marginalia\_nodes}}}{N_{\text{total\_additions\_in\_ground\_truth}}} \right) \times 100\%$$

$$\text{Content Retention Ratio} = \left( \frac{\text{Count}(\text{Marginalia Text Substrings Found in } T_{\text{dat}})}{N_{\text{extracted\_marginalia\_samples}}} \right) \times 100\%$$

---

## 3. Architecture & Software Quality Improvements

1. **Space-Efficient $O(\min(M,N))$ Levenshtein Engine:** Memory-optimized DP implementation with zero recursion.
2. **Text Normalization Pre-Processing:** Collapses whitespace and line breaks before comparison to prevent formatting noise from inflating distances.
3. **Multi-Factor Risk Assessment:** Evaluates risk across orthography, marginalia presence, and content retention with configurable thresholds.
4. **Comprehensive Unit Test Suite:** Includes `test_omni_auditor.py` covering all core metrics, edge cases, and XML schemas.
