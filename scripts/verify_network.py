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


def matmul(a, b, modulus):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) % modulus for j in range(3)] for i in range(3)]


def check_streams(states, seed):
    # Derive jumps from the one-step recurrence, independently of C jump constants.
    matrices = [[[0, 1, 0], [0, 0, 1], [-810728, 1403580, 0]],
                [[0, 1, 0], [0, 0, 1], [-1370589, 0, 527612]]]
    moduli = [4294967087, 4294944443]
    for c in range(2):
        for _ in range(127):
            matrices[c] = matmul(matrices[c], matrices[c], moduli[c])
    expected = [seed] * 6
    for row in states:
        if row["state"] != expected or row["draws"] != 0:
            raise AssertionError("MRG stream jump/initial state mismatch")
        expected = [sum(matrices[c][i][j] * expected[3*c+j] for j in range(3)) % moduli[c]
                    for c in range(2) for i in range(3)]


def check_recurrence(initial, final):
    for stream in range(4):
        s = initial[stream]["state"].copy()
        for _ in range(final[stream]["draws"] - initial[stream]["draws"]):
            p = (1403580*s[1] - 810728*s[0]) % 4294967087
            q = (527612*s[5] - 1370589*s[3]) % 4294944443
            s = [s[1], s[2], p, s[4], s[5], q]
        if s != final[stream]["state"]:
            raise AssertionError("MRG recurrence or draw accounting mismatch")


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
    report = {"status": "verification_and_plausibility_only", "rng": "MRG32k3a", "replicas_per_empty_scenario": args.replicas,
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
