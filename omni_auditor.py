"""
OMNI-Audit: Orthographic & Marginalia Normalization Integrity Auditor (v2.0.0)
================================================================================
Author: Dr. Rita Tegon (rita.tegon@usal.es)
Project: OMNI-Audit (Orthographic & Marginalia Normalization Integrity Auditor)
License: Creative Commons Attribution 4.0 International (CC BY 4.0)

An open-source, research-grade software instrument for evaluating Orthographic
Normalization, Marginalia Content Loss, and Algorithmic Distortion in Handwritten
Text Recognition (HTR) and crowdsourced archival transcription pipelines.
"""

import os
import re
import difflib
import json
import logging
import argparse
import statistics
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Optional, Any, Union

# Configure logger
logger = logging.getLogger("omni_audit")


# ==============================================================================
# 1. TEXT PREPROCESSING & WEIGHTED EDIT DISTANCE ENGINE
# ==============================================================================

class TextNormalizer:
    """Provides utility methods for text cleaning and normalization prior to audit."""

    @staticmethod
    def collapse_whitespace(text: str) -> str:
        """Collapses consecutive spaces, tabs, and newlines into a single space."""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text).strip()

    @staticmethod
    def remove_punctuation(text: str) -> str:
        """Removes punctuation marks to isolate lexical and orthographic content."""
        if not text:
            return ""
        return re.sub(r'[^\w\s]', '', text)


class WeightedEditDistance:
    """
    High-performance Levenshtein Edit Distance engine with custom character substitution
    costs tailored for historical manuscript orthography (e.g., u/v, i/j, long s, brevigraphs).
    """

    # Historical orthographic equivalences receiving reduced distance penalties
    HISTORICAL_EQUIVALENCES = {
        ('u', 'v'), ('v', 'u'),
        ('i', 'j'), ('j', 'i'),
        ('ſ', 's'), ('s', 'ſ'),
        ('f', 's'), ('s', 'f'),
        ('æ', 'ae'), ('ae', 'æ'),
        ('œ', 'oe'), ('oe', 'œ'),
        ('y', 'i'), ('i', 'y'),
        ('th', 'þ'), ('þ', 'th'),
        ('dh', 'ð'), ('ð', 'dh')
    }

    @classmethod
    def get_substitution_cost(cls, char1: str, char2: str, case_sensitive: bool = False) -> float:
        """Returns substitution penalty: 0.0 for match, 0.25 for historical variant, 1.0 for noise."""
        if char1 == char2:
            return 0.0
        if not case_sensitive and char1.lower() == char2.lower():
            return 0.1  # Case-only variation cost
        c1, c2 = (char1, char2) if case_sensitive else (char1.lower(), char2.lower())
        if (c1, c2) in cls.HISTORICAL_EQUIVALENCES:
            return 0.25  # Historical orthographic equivalence cost
        return 1.0  # Standard substitution cost

    @classmethod
    def compute(cls, s1: str, s2: str, case_sensitive: bool = False, weighted: bool = True) -> float:
        """
        Computes memory-efficient $O(\\min(M,N))$ space iterative edit distance.
        weighted=True  -> historical variants and case differences receive reduced costs.
        weighted=False -> standard (unweighted) Levenshtein distance: every edit costs 1.0.
        """
        if s1 == s2:
            return 0.0
        if not s1:
            return float(len(s2))
        if not s2:
            return float(len(s1))

        if len(s1) < len(s2):
            s1, s2 = s2, s1

        len_s2 = len(s2)
        previous_row = [float(i) for i in range(len_s2 + 1)]

        for i, c1 in enumerate(s1):
            current_row = [float(i + 1)] + [0.0] * len_s2
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1.0
                deletions = current_row[j] + 1.0
                if weighted:
                    sub_cost = cls.get_substitution_cost(c1, c2, case_sensitive)
                else:
                    sub_cost = 0.0 if c1 == c2 else 1.0
                substitutions = previous_row[j] + sub_cost
                current_row[j + 1] = min(insertions, deletions, substitutions)
            previous_row = current_row

        return previous_row[-1]


class OrthographicClassifier:
    """
    Token-level classifier separating orthographic normalisation from other changes.

    Each word of the diplomatic text is aligned with the datafied text. Changed words are
    classified as:
      * rule-based normalisation: the two forms become identical after historical folding
        (long s / f, u/v, i/j, y/i, thorn, ligatures, abbreviations such as ye/the and &/and,
        Roman numerals, doubled consonants, final silent -e, capitalisation);
      * probable normalisation: after folding, one form equals the other plus or minus vowels
        only (e.g. heyres -> heirs, wrayten -> written);
      * other change: any other altered word (e.g. recognition or transcription errors).
    Omitted and inserted words are counted separately, as content loss rather than spelling.

    ONI = (rule-based + probable normalisations) / all altered words
        (normalisations + other changes; omissions and insertions excluded).
    The classification is heuristic and intended as a diagnostic signal, not a verdict.
    """

    LEXICAL_EQUIVALENCES = {
        "ye": "the", "yᵉ": "the", "þe": "the", "yt": "that", "yᵗ": "that", "þt": "that",
        "wt": "with", "wᵗ": "with", "&": "and", "⁊": "and",
    }
    CHAR_FOLDS = [
        ("ſ", "s"), ("f", "s"), ("þ", "th"), ("ð", "th"), ("æ", "ae"), ("œ", "oe"),
        ("v", "u"), ("j", "i"), ("y", "i"),
    ]
    ROMAN = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}
    VOWELS = set("aeiou")
    MAX_EXAMPLES = 15

    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        return re.findall(r"[\w'ſþðæœ]+|&|⁊", text, flags=re.UNICODE)

    @classmethod
    def roman_to_int(cls, token: str) -> Optional[int]:
        t = token.lower()
        if not t or any(c not in cls.ROMAN for c in t) or t == "i":
            return None
        total, prev = 0, 0
        for c in reversed(t):
            v = cls.ROMAN[c]
            total = total - v if v < prev else total + v
            prev = max(prev, v)
        return total

    @classmethod
    def fold(cls, token: str) -> str:
        """Maps a word to a canonical form in which historical spelling variants coincide."""
        t = token.lower()
        if t in cls.LEXICAL_EQUIVALENCES:
            t = cls.LEXICAL_EQUIVALENCES[t]
        if token.isupper() and len(token) <= 6:
            n = cls.roman_to_int(token)
            if n is not None:
                return str(n)
        for a, b in cls.CHAR_FOLDS:
            t = t.replace(a, b)
        t = re.sub(r"([b-df-hj-np-tv-z])\1+", r"\1", t)   # undouble consonants
        if len(t) > 3 and t.endswith("e"):                # final silent -e
            t = t[:-1]
        return t

    @classmethod
    def differs_only_by_vowels(cls, a: str, b: str) -> bool:
        """True if the shorter string is obtained from the longer by deleting vowels only."""
        if a == b:
            return False
        longer, shorter = (a, b) if len(a) >= len(b) else (b, a)
        it = iter(longer)
        extra = []
        for ch in shorter:
            for c in it:
                if c == ch:
                    break
                extra.append(c)
            else:
                return False
        extra.extend(it)
        return bool(extra) and all(c in cls.VOWELS for c in extra)

    @classmethod
    def classify(cls, diplomatic: str, datafied: str) -> Dict[str, Any]:
        dip = cls.tokenize(diplomatic)
        dat = cls.tokenize(datafied)
        fdip = [cls.fold(t) for t in dip]
        fdat = [cls.fold(t) for t in dat]

        rule, probable, other, omitted, inserted = 0, 0, 0, 0, 0
        examples: List[Dict[str, str]] = []

        def note(kind: str, a: str, b: str):
            if len(examples) < cls.MAX_EXAMPLES:
                examples.append({"diplomatic": a, "datafied": b, "type": kind})

        sm = difflib.SequenceMatcher(a=fdip, b=fdat, autojunk=False)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal":
                for a, b in zip(dip[i1:i2], dat[j1:j2]):
                    if a != b:
                        rule += 1
                        note("orthographic (rule-based)", a, b)
            elif op == "replace":
                pairs = list(zip(range(i1, i2), range(j1, j2)))
                for i, j in pairs:
                    if cls.differs_only_by_vowels(fdip[i], fdat[j]):
                        probable += 1
                        note("orthographic (probable)", dip[i], dat[j])
                    else:
                        other += 1
                        note("other change", dip[i], dat[j])
                omitted += (i2 - i1) - len(pairs)
                inserted += (j2 - j1) - len(pairs)
            elif op == "delete":
                omitted += i2 - i1
                for a in dip[i1:i2]:
                    note("omission", a, "")
            elif op == "insert":
                inserted += j2 - j1
                for b in dat[j1:j2]:
                    note("insertion", "", b)

        altered = rule + probable + other
        oni = (rule + probable) / altered if altered else 0.0
        return {
            "oni_score": round(oni, 4),
            "status": "self_calibrated_calculated",
            "method": "token_level_normalisation_ratio",
            "diplomatic_tokens": len(dip),
            "altered_tokens": altered,
            "orthographic_rule_based": rule,
            "orthographic_probable": probable,
            "other_changes": other,
            "omitted_tokens": omitted,
            "inserted_tokens": inserted,
            "examples": examples,
        }


# ==============================================================================
# 2. CORE OMNI-AUDITOR ENGINE
# ==============================================================================

class OMNIAuditor:
    """
    Research-Grade Diagnostic Auditor for evaluating Archival Normalization,
    Marginalia Loss, and TEI Markup Integrity.
    """

    DEFAULT_THRESHOLDS = {
        "oni_moderate": 0.20,
        "oni_high": 0.45,
        "oni_critical": 0.70,
        "mpr_moderate": 90.0,
        "mpr_high": 75.0,
        "mpr_critical": 50.0,
    }

    def __init__(
        self,
        diplomatic_text: str = "",
        datafied_text: str = "",
        modernized_ref: str = "",
        thresholds: Optional[Dict[str, float]] = None,
        normalize_whitespace: bool = True
    ):
        self.raw_diplomatic = diplomatic_text or ""
        self.raw_datafied = datafied_text or ""
        self.raw_modernized = modernized_ref or ""
        
        self.thresholds = {**self.DEFAULT_THRESHOLDS, **(thresholds or {})}

        if normalize_whitespace:
            self.diplomatic = TextNormalizer.collapse_whitespace(self.raw_diplomatic)
            self.datafied = TextNormalizer.collapse_whitespace(self.raw_datafied)
            self.modernized = TextNormalizer.collapse_whitespace(self.raw_modernized)
        else:
            self.diplomatic = self.raw_diplomatic
            self.datafied = self.raw_datafied
            self.modernized = self.raw_modernized

    def calculate_cer_metrics(self) -> Dict[str, Any]:
        """Calculates Character Error Rate (CER), raw edit distance, and weighted edit distance."""
        if not self.diplomatic:
            return {
                "cer": 0.0,
                "raw_edit_distance": 0,
                "weighted_edit_distance": 0.0,
                "diplomatic_length": 0,
                "datafied_length": len(self.datafied)
            }

        raw_dist = WeightedEditDistance.compute(self.diplomatic, self.datafied, case_sensitive=True, weighted=False)
        weighted_dist = WeightedEditDistance.compute(self.diplomatic, self.datafied, case_sensitive=False, weighted=True)
        cer = raw_dist / max(len(self.diplomatic), 1)

        return {
            "cer": round(cer, 4),
            "raw_edit_distance": round(raw_dist, 2),
            "weighted_edit_distance": round(weighted_dist, 2),
            "diplomatic_length": len(self.diplomatic),
            "datafied_length": len(self.datafied)
        }

    def calculate_oni(self) -> Dict[str, Any]:
        """
        Calculates Orthographic Normalization Index (ONI) and Orthographic Drift Ratio.
        Measures the proportion of character changes that represent modernizing orthographic
        normalizations vs random corruption.
        """
        if not self.diplomatic or not self.datafied:
            return {
                "oni_score": 0.0,
                "status": "insufficient_input",
                "method": "none"
            }

        raw_dist = WeightedEditDistance.compute(self.diplomatic, self.datafied, case_sensitive=True, weighted=False)

        if raw_dist == 0:
            return {
                "oni_score": 0.0,
                "status": "perfect_match",
                "method": "exact_identity"
            }

        # Method A: Dual-Reference Calibration (When Modernized Reference is provided)
        if self.modernized:
            dist_dip_mod = WeightedEditDistance.compute(self.diplomatic, self.modernized, case_sensitive=False)
            dist_dat_mod = WeightedEditDistance.compute(self.datafied, self.modernized, case_sensitive=False)

            if dist_dip_mod == 0:
                oni_score = 0.0
            else:
                # Similarity convergence toward modernized text
                sim_dip_mod = 1.0 - (dist_dip_mod / max(len(self.diplomatic), len(self.modernized), 1))
                sim_dat_mod = 1.0 - (dist_dat_mod / max(len(self.datafied), len(self.modernized), 1))
                
                # Convergence index
                oni_score = max(0.0, min(1.0, (sim_dat_mod - sim_dip_mod) / max(1.0 - sim_dip_mod, 1e-5)))

            return {
                "oni_score": round(oni_score, 4),
                "status": "dual_reference_calculated",
                "method": "convergence_ratio",
                "dist_diplomatic_to_datafied": round(raw_dist, 2),
                "dist_diplomatic_to_modernized": round(dist_dip_mod, 2)
            }

        # Method B: Self-calibrated, token-level Orthographic Normalisation Ratio.
        # Every changed word is classified as an orthographic normalisation
        # (rule-based or probable) or as another change (recognition error, omission, insertion).
        return OrthographicClassifier.classify(self.diplomatic, self.datafied)

    def audit_tei_xml(self, tei_file_path: str) -> Dict[str, Any]:
        """
        Comprehensively parses TEI-P5 XML documents for marginalia tags across multiple schemas
        (<add place="margin">, <note place="margin">, <seg type="margin">, <zone>, etc.) and measures
        both tag retention and content preservation.
        """
        if not os.path.exists(tei_file_path):
            return {"error": f"File not found: {tei_file_path}"}

        try:
            tree = ET.parse(tei_file_path)
            root = tree.getroot()
        except Exception as e:
            return {"error": f"XML Parsing Error: {str(e)}"}

        # Define namespace handling
        namespaces = {
            'tei': 'http://www.tei-c.org/ns/1.0',
            'xml': 'http://www.w3.org/XML/1998/namespace'
        }

        def find_elements(tag_name: str) -> List[ET.Element]:
            elems = root.findall(f'.//tei:{tag_name}', namespaces)
            if not elems:
                elems = root.findall(f'.//{tag_name}')
            return elems

        all_additions = find_elements('add')
        all_notes = find_elements('note')
        all_deletions = find_elements('del')
        all_abbreviations = find_elements('abbr')
        all_expansions = find_elements('expan')
        all_choices = find_elements('choice')
        all_unclear = find_elements('unclear')
        all_supplied = find_elements('supplied')
        all_zones = find_elements('zone')

        # Filter marginalia nodes across multiple TEI conventions
        margin_places = {'margin', 'left', 'right', 'above', 'below', 'head', 'foot'}
        
        margin_additions = [a for a in all_additions if a.attrib.get('place', '').lower() in margin_places]
        margin_notes = [n for n in all_notes if n.attrib.get('place', '').lower() in margin_places or n.attrib.get('type', '').lower() == 'marginal']
        margin_zones = [z for z in all_zones if z.attrib.get('type', '').lower() == 'margin']

        total_marginalia_nodes = len(margin_additions) + len(margin_notes) + len(margin_zones)
        total_ground_truth_additions = len(all_additions) + len(all_notes)

        # Extract text content from marginalia nodes
        marginalia_texts = []
        for elem in margin_additions + margin_notes + margin_zones:
            text_content = "".join(elem.itertext()).strip()
            if text_content:
                marginalia_texts.append(text_content)

        # Evaluate Marginalia Preservation Ratio (MPR)
        if total_ground_truth_additions == 0:
            mpr_percentage = 100.0
            has_marginalia_in_ground_truth = False
        else:
            mpr_percentage = (total_marginalia_nodes / total_ground_truth_additions) * 100.0
            has_marginalia_in_ground_truth = total_marginalia_nodes > 0

        # Check marginalia content retention in datafied text stream
        content_retained_count = 0
        if self.datafied and marginalia_texts:
            for text in marginalia_texts:
                if text in self.datafied or TextNormalizer.collapse_whitespace(text) in self.datafied:
                    content_retained_count += 1
            content_retention_ratio = (content_retained_count / len(marginalia_texts)) * 100.0
        else:
            content_retention_ratio = 100.0 if not marginalia_texts else 0.0

        return {
            "has_marginalia_in_ground_truth": has_marginalia_in_ground_truth,
            "mpr_percentage": round(mpr_percentage, 2),
            "content_retention_ratio": round(content_retention_ratio, 2),
            "tag_breakdown": {
                "margin_additions": len(margin_additions),
                "margin_notes": len(margin_notes),
                "margin_zones": len(margin_zones),
                "total_additions": len(all_additions),
                "total_deletions": len(all_deletions),
                "total_abbreviations": len(all_abbreviations),
                "total_expansions": len(all_expansions),
                "choice_structures": len(all_choices),
                "unclear_tokens": len(all_unclear),
                "supplied_tokens": len(all_supplied)
            },
            "extracted_marginalia_samples": marginalia_texts[:5]  # Sample first 5
        }

    def evaluate_line_by_line_statistics(self) -> Dict[str, Any]:
        """Calculates line-level Character Error Rate (CER) distribution and statistics."""
        if not self.raw_diplomatic or not self.raw_datafied:
            return {"status": "insufficient_data"}

        dip_lines = self.raw_diplomatic.splitlines()
        dat_lines = self.raw_datafied.splitlines()

        min_len = min(len(dip_lines), len(dat_lines))
        if min_len == 0:
            return {"status": "empty_lines"}

        line_cers = []
        for i in range(min_len):
            line_dip = TextNormalizer.collapse_whitespace(dip_lines[i])
            line_dat = TextNormalizer.collapse_whitespace(dat_lines[i])
            if line_dip:
                dist = WeightedEditDistance.compute(line_dip, line_dat, case_sensitive=True, weighted=False)
                cer = dist / len(line_dip)
                line_cers.append(cer)

        if not line_cers:
            return {"status": "no_valid_lines"}

        return {
            "line_count_evaluated": len(line_cers),
            "mean_cer": round(statistics.mean(line_cers), 4),
            "median_cer": round(statistics.median(line_cers), 4),
            "stdev_cer": round(statistics.stdev(line_cers), 4) if len(line_cers) > 1 else 0.0,
            "min_cer": round(min(line_cers), 4),
            "max_cer": round(max(line_cers), 4)
        }

    def evaluate_risk_level(self, oni_score: float, xml_audit: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates overall risk category using a multi-factor diagnostic matrix.
        """
        mpr_val = xml_audit.get("mpr_percentage", 100.0)
        has_marginalia = xml_audit.get("has_marginalia_in_ground_truth", True)
        content_retention = xml_audit.get("content_retention_ratio", 100.0)

        risk_scores = []
        recommendations = []

        # ONI Risk Evaluation
        if oni_score >= self.thresholds["oni_critical"]:
            risk_scores.append(3)  # Critical Risk
            recommendations.append("Critical Orthographic Normalization: Silent modernization is severely altering historical manuscript spellings.")
        elif oni_score >= self.thresholds["oni_high"]:
            risk_scores.append(2)  # High Risk
            recommendations.append("High Orthographic Drift: Significant conversion of archaic letterforms to modern standard spelling.")
        elif oni_score >= self.thresholds["oni_moderate"]:
            risk_scores.append(1)  # Moderate Risk
            recommendations.append("Moderate Orthographic Variation: Minor modernization detected in common vocabulary.")
        else:
            risk_scores.append(0)  # Low Risk

        # Marginalia Risk Evaluation (Only if marginalia exist in ground truth)
        if has_marginalia:
            if mpr_val < self.thresholds["mpr_critical"] or content_retention < 50.0:
                risk_scores.append(3)
                recommendations.append("Critical Marginalia Erasure: Over 50% of manuscript margin notes/glosses have been omitted or un-tagged.")
            elif mpr_val < self.thresholds["mpr_high"] or content_retention < 75.0:
                risk_scores.append(2)
                recommendations.append("High Marginalia Loss: Multiple spatial annotations were skipped during HTR line segmentation.")
            elif mpr_val < self.thresholds["mpr_moderate"]:
                risk_scores.append(1)
                recommendations.append("Moderate Layout Loss: Ensure TEI <add place='margin'> or <note> tags are consistently assigned.")

        max_risk = max(risk_scores) if risk_scores else 0

        risk_labels = {
            0: ("LOW RISK / ARCHIVAL GRADE", "GREEN"),
            1: ("MODERATE RISK / MINOR DRIFT", "YELLOW"),
            2: ("HIGH RISK / DATA DISTORTION", "ORANGE"),
            3: ("CRITICAL RISK / ERASURE HAZARD", "RED")
        }

        level_name, color = risk_labels[max_risk]
        if max_risk == 0:
            recommendations.append("High diplomatic fidelity maintained. Text and layout integrity preserved.")

        return {
            "risk_score_numeric": max_risk,
            "risk_level": level_name,
            "color_code": color,
            "recommendations": recommendations
        }

    def generate_full_report(self, tei_file_path: Optional[str] = None) -> Dict[str, Any]:
        """Generates a complete research-grade diagnostic audit report."""
        cer_metrics = self.calculate_cer_metrics()
        oni_data = self.calculate_oni()

        xml_audit = {}
        if tei_file_path:
            xml_audit = self.audit_tei_xml(tei_file_path)

        risk_eval = self.evaluate_risk_level(oni_data["oni_score"], xml_audit)
        line_stats = self.evaluate_line_by_line_statistics()

        report = {
            "tool": "OMNI-Audit: Orthographic & Marginalia Normalization Integrity Auditor",
            "version": "2.0.0",
            "author": "Dr. Rita Tegon (rita.tegon@usal.es)",
            "license": "CC BY 4.0",
            "metrics": {
                "orthographic_normalization_index_oni": oni_data["oni_score"],
                "character_error_rate_cer": cer_metrics["cer"],
                "raw_edit_distance": cer_metrics["raw_edit_distance"],
                "weighted_edit_distance": cer_metrics["weighted_edit_distance"],
                "oni_calculation_details": oni_data
            },
            "line_statistics": line_stats,
            "xml_markup_audit": xml_audit,
            "risk_assessment": risk_eval
        }
        return report


# ==============================================================================
# 3. CLI ENTRYPOINT
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="OMNI-Audit v2.0: Orthographic & Marginalia Normalization Integrity Auditor")
    parser.add_argument("--diplomatic", type=str, help="Path to ground-truth diplomatic text file")
    parser.add_argument("--datafied", type=str, help="Path to OCR/HTR or crowdsourced datafied text file")
    parser.add_argument("--modernized", type=str, help="Path to optional modernized reference text file")
    parser.add_argument("--tei-xml", type=str, help="Path to TEI-XML manuscript export file")
    parser.add_argument("--output-json", type=str, help="Path to save output JSON audit report")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging output")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    dip_text = ""
    dat_text = ""
    mod_text = ""

    if args.diplomatic and os.path.exists(args.diplomatic):
        with open(args.diplomatic, "r", encoding="utf-8") as f:
            dip_text = f.read()

    if args.datafied and os.path.exists(args.datafied):
        with open(args.datafied, "r", encoding="utf-8") as f:
            dat_text = f.read()

    if args.modernized and os.path.exists(args.modernized):
        with open(args.modernized, "r", encoding="utf-8") as f:
            mod_text = f.read()

    auditor = OMNIAuditor(dip_text, dat_text, mod_text)
    report = auditor.generate_full_report(tei_file_path=args.tei_xml)

    report_json = json.dumps(report, indent=2, ensure_ascii=False)

    print("\n==================================================================")
    print("      OMNI-AUDIT v2.0: ARCHIVAL NORMALIZATION INTEGRITY REPORT     ")
    print("==================================================================")
    print(report_json)
    print("==================================================================\n")

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            f.write(report_json)
        print(f"Report saved to: {args.output_json}")


if __name__ == "__main__":
    main()
