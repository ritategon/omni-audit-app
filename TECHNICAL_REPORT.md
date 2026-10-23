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

### B. Orthographic Normalization Index ($\text{ONI}$)

**Method 1 — Self-calibrated, token-level (default).** The diplomatic and datafied texts are split into words and aligned. Each word is first mapped to a *folded* canonical form in which historical variants coincide: long s and f→s, u/v, i/j, y/i, thorn and eth→th, æ/œ, abbreviations (*ye*/*the*, *yt*/*that*, *wt*/*with*, *&*/*and*), Roman numerals→Arabic, doubled consonants, final silent *-e* and capitalisation. Each altered word is then classified as:

* **rule-based normalisation:** identical to its counterpart after folding (e.g. *fcripture → scripture*, *ye → the*, *V → 5*);
* **probable normalisation:** after folding, differs from its counterpart only by added or removed vowels (e.g. *heyres → heirs*, *wrayten → written*);
* **other change:** any other alteration, typically a recognition or transcription error (e.g. *name → narne*).

Omitted and inserted words are counted separately as content loss.

$$\text{ONI} = \frac{N_{\text{rule-based}} + N_{\text{probable}}}{N_{\text{rule-based}} + N_{\text{probable}} + N_{\text{other}}}$$

* **Interpretation:** $\text{ONI} = 0.0$: no altered word is a spelling modernisation (only errors, or no changes); $\text{ONI} = 1.0$: every altered word is a spelling modernisation. The classification is heuristic and should be read together with the list of classified examples in the report.

**Method 2 — Dual reference (when a modernised reference text is supplied).** ONI measures how far the datafied text has converged from the diplomatic text toward the modernised reference.

The weighted Levenshtein distance (section A) is reported alongside the standard (unweighted) distance used for the Character Error Rate.

### C. Marginalia Preservation & Content Retention Ratio ($\text{MPR}$)
The parser evaluates both tag retention and textual content presence across multiple TEI-P5 elements (`<add place="margin|left|right|above">`, `<note place="margin">`, `<zone type="margin">`):

$$\text{MPR} = \left( \frac{N_{\text{captured\_marginalia\_nodes}}}{N_{\text{total\_additions\_in\_ground\_truth}}} \right) \times 100\%$$

$$\text{Content Retention Ratio} = \left( \frac{\text{Count}(\text{Marginalia Text Substrings Found in } T_{\text{dat}})}{N_{\text{extracted\_marginalia\_samples}}} \right) \times 100\%$$

---

## 3. Architecture & Software Quality Improvements

1. **Space-Efficient $O(\min(M,N))$ Levenshtein Engine:** Memory-optimized DP implementation with zero recursion.
2. **Text Normalization Pre-Processing:** Collapses whitespace and line breaks before comparison to prevent formatting noise from inflating distances.
3. **Multi-Factor Risk Assessment:** Evaluates risk across orthography, marginalia presence, and content retention with configurable thresholds.
4. **Unit Test Suite:** `test_omni_auditor.py` (13 tests) covers the edit distances, both ONI methods (including recognition errors and omissions), TEI parsing and risk evaluation.
