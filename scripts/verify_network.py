"""Phase 3 smoke runs and trajectory-factor diagnostics, never production."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time
from export_simulation import export, ROOT


OFFSETS = [0, 800000000, 1600000000, 1900000000]
LENGTHS = [800000000, 800000000, 300000000, 247483646]
MODULUS = 2147483647


def check_streams(states, seed, expected_draws=0):
    if len(states) != 4:
        raise AssertionError("Expected exactly four Lehmer network streams")
    for i, row in enumerate(states):
        count = row["draws"]
        if (row.get("stream") != i or row.get("offset") != OFFSETS[i] or
            row.get("limit") != LENGTHS[i]-1 or count < 0 or count >= LENGTHS[i] or
            (expected_draws is not None and count != expected_draws) or
            row["state"] != seed*pow(48271, OFFSETS[i]+count, MODULUS) % MODULUS):
            raise AssertionError("Lehmer block, state, count or jump mismatch")


def check_recurrence(initial, final):
    if len(initial) != 4 or len(final) != 4:
        raise AssertionError("Expected four states")
    for a, b in zip(initial, final):
        count = b["draws"]-a["draws"]
        if count < 0 or b["state"] != a["state"]*pow(48271, count, MODULUS) % MODULUS:
            raise AssertionError("Lehmer recurrence or draw accounting mismatch")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=ROOT / "build/debug/rome_bus_pmcsn.exe")
    parser.add_argument("--replicas", type=int, default=4)
    args = parser.parse_args()
    if args.replicas < 2:
        parser.error("At least two diagnostic replicas required")
    directory = ROOT / "data/processed/phase3/verification"
    directory.mkdir(parents=True, exist_ok=True)
    cases = []
    for scenario in ("BASE", "D075", "D125", "REGULAR", "SHARED", "SHARED_D125"):
        for loaded in (False, True):
            name = scenario + ("_loaded" if loaded else "_empty")
            path = directory / (name + ".txt")
            export(scenario, loaded, path)
            replicas = 1 if loaded else args.replicas
            rows = []
            # One process continues all streams across these replicas.
            command = [str(args.exe.resolve()), "simulate", "network", str(path), "--replicas", str(replicas)]
            started = time.perf_counter()
            run = subprocess.run(command, capture_output=True, text=True, check=True)
            elapsed = time.perf_counter()-started
            output = [json.loads(line) for line in run.stdout.splitlines()]
            check_streams(output[0]["rng_initial"], 123456789)
            check_recurrence(output[0]["rng_initial"], output[-1]["rng_final"])
            check_streams(output[-1]["rng_final"], 123456789, expected_draws=None)
            for i, row in enumerate(output):
                if i and row["rng_initial"] != output[i-1]["rng_final"]:
                    raise AssertionError("Streams reset between replicas")
                if row["arrivals"] != row["boarded"] + row["unserved"]:
                    raise AssertionError("Passenger balance")
                rows.append({k: row[k] for k in ("arrivals", "boarded", "unserved", "completed", "onboard",
                                                "reserved", "mean_wait", "queue_area", "restricted_wait_sum", "environment_keys")})
            (directory / (name + ".jsonl")).write_text(run.stdout, encoding="utf-8")
            # Reproduce first replica with a trace to inspect selected (including reused) factors.
            trace = directory / (name + ".csv")
            if trace.exists():
                trace.unlink()  # Only this script's explicit generated artifact, not user input.
            traced = subprocess.run([str(args.exe.resolve()), "simulate", "network", str(path), "--trace", str(trace)],
                                    capture_output=True, text=True, check=True)
            if json.loads(traced.stdout) != output[0]:
                raise AssertionError("Trace changed simulation or reproduction failed")
            factors = []
            sample_times = set()
            with trace.open() as f:
                for record in csv.DictReader(f):
                    if record["type"] == "travel_factor":
                        factors.append(float(record["value"]))
                    if record["type"] == "queue_primary":
                        sample_times.add(float(record["time"]))
            mean = sum(factors) / len(factors)
            cv = math.sqrt(sum((x-mean)**2 for x in factors) / len(factors)) / mean
            factor_diagnostic = {"traversals": len(factors), "mean": mean, "cv": cv,
                                 "within_prespecified_smoke_tolerance": abs(mean-1) <= .02 and abs(cv-(0 if scenario == "REGULAR" else .2)) <= .03}
            if len(sample_times) != 49:
                raise AssertionError("Missing 300s samples or final snapshot")
            cases.append({"scenario": scenario, "loaded": loaded, "replicas": replicas, "metrics": rows,
                          "wall_seconds": elapsed,
                          "selected_factor_first_replica": factor_diagnostic,
                          "cumulative_stream_draws": [x["draws"] for x in output[-1]["rng_final"][:5]],
                          "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            print(name, "passed", file=sys.stderr)
    report = {"status": "verification_and_plausibility_only", "rng": "lehmer48271-m2147483647-network-partition-v2", "replicas_per_empty_scenario": args.replicas,
              "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in [*sorted((ROOT / "src/simulation").glob("*.c")),
                                          ROOT / "include/rome_bus_pmcsn/simulation.h", ROOT / "scripts/export_simulation.py",
                                          ROOT / "scripts/verify_network.py"]},
              "exe_sha256": hashlib.sha256(args.exe.read_bytes()).hexdigest(), "cases": cases,
              "all_factor_smoke_checks_passed": all(c["selected_factor_first_replica"]["within_prespecified_smoke_tolerance"] for c in cases),
              "limitations": ["Separate reproducibility campaigns reuse root seed; no independent scenario contrasts computed",
                              "Factor moment smoke checks are descriptive, do not prove distributional equivalence",
                              "Initial states and passenger demand are synthetic; no empirical validation",
                              "No transient study, pilot, production or confidence-interval result"]}
    (ROOT / "reports/phase3_network_checks.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not report["all_factor_smoke_checks_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
