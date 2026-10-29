"""Instrumentation, shared keys, independent keys and batch continuation."""
import copy
import argparse
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--exe", type=Path, default=ROOT / "build/debug/rome_bus_pmcsn.exe")
args, rest = parser.parse_known_args()
EXE = args.exe.resolve()
sys.path.insert(0, str(ROOT / "scripts"))
from verify_network import check_streams, check_recurrence


class TravelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gate38-tests-", dir=ROOT / "build")
        self.directory = Path(self.temp.name)
        # Verify the recursive cleanup target is inside the test workspace.
        self.assertTrue(self.directory.resolve().is_relative_to((ROOT / "build").resolve()))

    def tearDown(self):
        self.temp.cleanup()

    def fixture(self, mode):
        path = self.directory / f"mode{mode}.txt"
        path.write_text(f"PMNET1 0 10 0.2 {mode}\n0 2\n"
                        "R 0 A 1 2 0 0 1\n0 1 1 1 1 common\n1 2 0 1 0 -\n"
                        "S 0 B 1 2 0 0 1\n0 1 1 1 1 common\n1 2 0 1 0 -\n0\n", encoding="ascii")
        return path

    def run_cli(self, *arguments):
        return subprocess.run([str(EXE), *map(str, arguments)], capture_output=True, text=True, check=True)

    def test_trace_is_observational_and_records_reuse(self):
        for mode in (0, 1):
            path = self.fixture(mode)
            normal = self.run_cli("simulate", "network", path, "--replicas", 2)
            travel = self.directory / f"travel{mode}.csv"
            traced = self.run_cli("simulate", "network", path, "--replicas", 2, "--travel-trace", travel)
            self.assertEqual(normal.stdout, traced.stdout)
            with travel.open() as f:
                records = list(csv.DictReader(f))
            self.assertEqual(len(records), 4)
            self.assertEqual([int(r["replica"]) for r in records], [0, 0, 1, 1])
            self.assertEqual([int(r["reused"]) for r in records], [0, mode, 0, mode])
            self.assertEqual(records[0]["factor"] == records[1]["factor"], bool(mode))
            result = json.loads(traced.stdout.splitlines()[0])
            self.assertEqual(result["rng_final"][3 if mode else 2]["draws"], 2 if mode else 4)
            if mode:
                self.assertEqual(records[0]["environment_key"], "|common")
            else:
                self.assertEqual(records[0]["environment_key"], "R|common")
                self.assertEqual(records[1]["environment_key"], "S|common")
            for row in records:
                self.assertAlmostEqual(float(row["duration"]), float(row["reference"])*float(row["factor"]))
            denied = subprocess.run([str(EXE), "simulate", "network", str(path), "--travel-trace", str(travel)], capture_output=True)
            self.assertNotEqual(denied.returncode, 0)

    def test_campaign_continues_at_case_boundary(self):
        first, second = self.fixture(0), self.fixture(1)
        plan = self.directory / "plan with spaces.txt"
        plan.write_text(f"PMDIAG1 2 2 10\n{first}\n{second}\n", encoding="ascii")
        travel = self.directory / "batch.csv"
        output = self.run_cli("diagnose", "network", plan, "--travel-trace", travel)
        rows = [json.loads(line) for line in output.stdout.splitlines()]
        self.assertEqual([r["replica"] for r in rows], list(range(4)))
        self.assertEqual([r["rng_initial"][s]["draws"] for s in range(4) for r in rows[:1]], [10]*4)
        for a, b in zip(rows, rows[1:]):
            self.assertEqual(a["rng_final"], b["rng_initial"])
        with travel.open() as f:
            self.assertEqual(len(list(csv.DictReader(f))), 8)

    def test_full_period_and_partition(self):
        period = 2147483646
        self.assertEqual(2*3*3*7*11*31*151*331, period)
        self.assertEqual(pow(48271, period, period+1), 1)
        for prime in (2, 3, 7, 11, 31, 151, 331):
            self.assertNotEqual(pow(48271, period//prime, period+1), 1)
        from verify_network import OFFSETS, LENGTHS
        self.assertEqual(OFFSETS, [sum(LENGTHS[:i]) for i in range(4)])
        self.assertEqual(sum(LENGTHS), period)

    def test_lehmer_partition_and_jump_against_python(self):
        path = self.fixture(0)
        for seed in (1, 12345, 123456789, 2147483646):
            row = json.loads(self.run_cli("simulate", "network", path, "--seed", seed).stdout)
            self.assertEqual(row["rng_version"], "lehmer48271-m2147483647-network-partition-v2")
            check_streams(row["rng_initial"], seed)
            check_streams(row["rng_final"], seed, expected_draws=None)
            check_recurrence(row["rng_initial"], row["rng_final"])
            bad = copy.deepcopy(row["rng_final"])
            bad[2]["state"] = bad[2]["state"] % 2147483646 + 1
            with self.assertRaises(AssertionError):
                check_streams(bad, seed, expected_draws=None)
        for seed in (0, 2147483647, 4294944442):
            result = subprocess.run([str(EXE), "simulate", "network", str(path), "--seed", str(seed)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, b"")

    def test_regular_uses_no_environment_draws(self):
        path = self.fixture(0)
        path.write_text(path.read_text().replace("0.2 0", "0 0"))
        travel = self.directory / "regular.csv"
        row = json.loads(self.run_cli("simulate", "network", path, "--travel-trace", travel).stdout)
        self.assertEqual(row["rng_initial"], row["rng_final"])
        with travel.open() as f:
            records = list(csv.DictReader(f))
        self.assertTrue(all(r["factor"] == "1" and r["factor_index"] == "-1" for r in records))


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0], *rest])
