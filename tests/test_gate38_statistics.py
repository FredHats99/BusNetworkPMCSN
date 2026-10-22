"""Analytic quantile references and equivalence-decision edge cases."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from gate38_statistics import assess, student_critical, student_upper_tail


class StatisticsTests(unittest.TestCase):
    def test_cauchy_exact(self):
        for tail in (.1, .05, .025, .00001):
            self.assertAlmostEqual(student_critical(1, tail)/math.tan(math.pi*(.5-tail)), 1, places=9)

    def test_student_reference_values(self):
        self.assertAlmostEqual(student_critical(9, .025), 2.2621571628540993, places=9)
        self.assertAlmostEqual(student_critical(31, .025), 2.0395134463964077, places=10)
        self.assertAlmostEqual(student_upper_tail(0, 31), .5)

    def test_equivalence_and_missing(self):
        self.assertEqual(assess([1.0]*32, 1, .02, 1000, .95, 32)["status"], "passed")
        self.assertEqual(assess([1.1]*32, 1, .02, 1000, .95, 32)["status"], "failed")
        self.assertEqual(assess([.125]*32, 0, .125, 1000, .95, 32)["status"], "inconclusive")
        self.assertEqual(assess([None]+[1.0]*31, 1, .02, 1000, .95, 32)["reason"], "insufficient_coverage")
        self.assertEqual(assess([.8, 1.2]*16, 1, .02, 1000, .95, 32)["status"], "inconclusive")

    def test_family_penalty(self):
        self.assertGreater(student_critical(31, .05/(2*1000)), student_critical(31, .025))


if __name__ == "__main__":
    unittest.main()
