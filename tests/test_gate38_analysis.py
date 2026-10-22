"""Fixed inventory and replica aggregation: no empirical selection of groups."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from gate38 import Accumulator, inventory


class AnalysisTests(unittest.TestCase):
    def test_replica_statistics(self):
        acc = Accumulator([1.0])
        acc.add(.8, 100, 80)
        acc.add(1.2, 200, 240)
        row = acc.finish([.5])
        self.assertEqual(row["mean"], 1)
        self.assertAlmostEqual(row["cv"], .2)
        self.assertEqual(row["cdf_0.5"], .5)
        self.assertEqual(row["mean_delta"], 10)
        self.assertEqual(row["mean_duration"], 160)
        self.assertEqual(row["mean_reference"], 150)

    def test_cv_of_single_pass_is_unavailable(self):
        acc = Accumulator([1.0])
        acc.add(1.1, 100, 110)
        self.assertIsNone(acc.finish([.5])["cv"])

    def test_inventory_contains_all_arcs_before_observations(self):
        c = json.loads((ROOT / "configs/gate38_criteria.json").read_text())
        cases = [dict(id=f"{s}|{mode}", scenario=s) for s in c["scenarios"] for mode in c["initializations"]]
        arcs = ["arc|R|0|0|1", "arc|R|0|1|2"]
        groups = ["network", "line|R|0", "domain|inside"]
        items = inventory(c, cases, arcs, groups)
        self.assertEqual(len(items), 14*len(groups)*7+18*len(arcs))
        self.assertEqual(sum(i["kind"] == "reference_arc_time" for i in items), 12*len(arcs))
        self.assertFalse(any(i["kind"] == "reference_marginal" and i["case"].startswith("REGULAR|") for i in items))
        self.assertEqual({i["group"] for i in items if i["kind"] == "reference_arc_time"}, set(arcs))


if __name__ == "__main__":
    unittest.main()
