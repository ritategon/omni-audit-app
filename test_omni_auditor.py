"""
Unit Test Suite for OMNI-Audit (v2.0.0)
========================================
Author: Dr. Rita Tegon (rita.tegon@usal.es)
Runs with standard Python unittest framework.
"""

import unittest
import os
import tempfile
from omni_auditor import OMNIAuditor, WeightedEditDistance, TextNormalizer


class TestWeightedEditDistance(unittest.TestCase):

    def test_exact_match(self):
        dist = WeightedEditDistance.compute("manuscript", "manuscript")
        self.assertEqual(dist, 0.0)

    def test_historical_variant_discount(self):
        # u/v variant should have cost 0.25 vs standard substitution cost 1.0
        dist_uv = WeightedEditDistance.compute("have", "haue", case_sensitive=False)
        dist_xy = WeightedEditDistance.compute("have", "haxe", case_sensitive=False)
        self.assertEqual(dist_uv, 0.25)
        self.assertEqual(dist_xy, 1.0)
        self.assertLess(dist_uv, dist_xy)

    def test_long_s_variant(self):
        dist_s = WeightedEditDistance.compute("fcripture", "scripture", case_sensitive=False)
        self.assertEqual(dist_s, 0.25)


class TestTextNormalizer(unittest.TestCase):

    def test_whitespace_collapsing(self):
        raw = "  In   ye   name \n\n of   God   "
        clean = TextNormalizer.collapse_whitespace(raw)
        self.assertEqual(clean, "In ye name of God")


class TestOMNIAuditor(unittest.TestCase):

    def setUp(self):
        self.diplomatic = "In ye name of God, Amen. Thif fcripture wrayten in ye yeare 1584."
        self.datafied = "In the name of God, Amen. This scripture written in the year 1584."
        self.modernized = "In the name of God, Amen. This scripture written in the year 1584."

    def test_cer_calculation(self):
        auditor = OMNIAuditor(self.diplomatic, self.datafied)
        cer_data = auditor.calculate_cer_metrics()
        self.assertGreater(cer_data["cer"], 0.0)
        self.assertGreater(cer_data["raw_edit_distance"], 0)

    def test_oni_self_calibrated(self):
        auditor = OMNIAuditor(self.diplomatic, self.datafied)
        oni_data = auditor.calculate_oni()
        self.assertIn("oni_score", oni_data)
        self.assertGreaterEqual(oni_data["oni_score"], 0.0)
        self.assertLessEqual(oni_data["oni_score"], 1.0)

    def test_oni_detects_full_modernisation(self):
        # Fully modernised spelling must give a high ONI even without a modernised reference
        auditor = OMNIAuditor(self.diplomatic, self.datafied)
        oni_data = auditor.calculate_oni()
        self.assertEqual(oni_data["method"], "token_level_normalisation_ratio")
        self.assertGreaterEqual(oni_data["oni_score"], 0.9)
        self.assertGreater(oni_data["orthographic_rule_based"], 0)

    def test_oni_ignores_recognition_errors(self):
        # Recognition errors that keep the historical spelling must not count as normalisation
        htr = "In ye narne of Gud, Amen. Thif fcripture wrayten in ye yeare 1584."
        oni_data = OMNIAuditor(self.diplomatic, htr).calculate_oni()
        self.assertEqual(oni_data["oni_score"], 0.0)
        self.assertEqual(oni_data["other_changes"], 2)

    def test_oni_counts_omissions_separately(self):
        truncated = "In the name of God, Amen."
        oni_data = OMNIAuditor(self.diplomatic, truncated).calculate_oni()
        self.assertEqual(oni_data["oni_score"], 1.0)
        self.assertGreater(oni_data["omitted_tokens"], 0)

    def test_raw_distance_is_unweighted(self):
        self.assertEqual(WeightedEditDistance.compute("fcripture", "scripture", weighted=False), 1.0)
        auditor = OMNIAuditor(self.diplomatic, self.datafied)
        cer_data = auditor.calculate_cer_metrics()
        self.assertGreater(cer_data["raw_edit_distance"], cer_data["weighted_edit_distance"])

    def test_oni_dual_reference(self):
        auditor = OMNIAuditor(self.diplomatic, self.datafied, self.modernized)
        oni_data = auditor.calculate_oni()
        self.assertEqual(oni_data["method"], "convergence_ratio")
        self.assertGreaterEqual(oni_data["oni_score"], 0.0)

    def test_tei_xml_parsing(self):
        tei_content = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
          <text>
            <body>
              <p>
                In <choice><abbr>ye</abbr><expan>the</expan></choice> name of God.
                <add place="margin">Witnessed by Thomas Smith</add>
                <note place="margin">Margin annotation 2</note>
                <del rend="strikethrough">canceled text</del>
              </p>
            </body>
          </text>
        </TEI>"""

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".xml", encoding="utf-8") as f:
            f.write(tei_content)
            temp_path = f.name

        try:
            auditor = OMNIAuditor(self.diplomatic, self.datafied)
            xml_audit = auditor.audit_tei_xml(temp_path)
            self.assertTrue(xml_audit["has_marginalia_in_ground_truth"])
            self.assertEqual(xml_audit["tag_breakdown"]["margin_additions"], 1)
            self.assertEqual(xml_audit["tag_breakdown"]["margin_notes"], 1)
            self.assertEqual(xml_audit["tag_breakdown"]["total_deletions"], 1)
            self.assertEqual(xml_audit["tag_breakdown"]["total_abbreviations"], 1)
        finally:
            os.remove(temp_path)

    def test_risk_level_evaluation(self):
        auditor = OMNIAuditor(self.diplomatic, self.datafied)
        report = auditor.generate_full_report()
        self.assertIn("risk_assessment", report)
        self.assertIn("risk_level", report["risk_assessment"])


if __name__ == "__main__":
    unittest.main()
