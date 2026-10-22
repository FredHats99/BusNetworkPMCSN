"""Finite-horizon verification against Spitzer, using only Python stdlib.

No steady-state assumption, no warm-up removal, no production experiment.
The C simulator and this analytic reference share no queue implementation.
"""
import argparse
import json
import math
from pathlib import Path
import subprocess


def excess_poisson(mean, threshold):
    """Positive sum; stop with a geometric upper bound on remaining terms."""
    j = threshold + 1
    total = 0.0
    while True:
        term = (j - threshold) * math.exp(-mean + j * math.log(mean) - math.lgamma(j + 1))
        total += term
        ratio = mean / (j + 1) * (j + 1 - threshold) / (j - threshold)
        # Ratios decrease, so the uncomputed positive tail is bounded.
        if ratio < 1 and term * ratio / (1 - ratio) < 1e-13:
            return total
        j += 1
        if j > 100000:
            raise RuntimeError("Poisson reference failed to converge")


def reference(rate, h, c, cycles):
    a = rate * h
    ex = [0.0]
    for n in range(1, cycles):
        ex.append(ex[-1] + excess_poisson(n * a, n * c) / n)
    # Horizon is exclusive: the last bus is at (K-1)h, not Kh.
    return {"residual": ex[-1] + a, "mean_queue": sum(ex) / cycles + a / 2}


def verify(exe, replicas):
    cases = []
    for rate in (0.2, 0.8, 1.2):
        expected = reference(rate, 10, 10, 20)
        accum = {k: [0, 0.0, 0.0] for k in expected}
        command = [str(exe), "simulate", "controlled", "--rate", str(rate),
                   "--headway", "10", "--capacity", "10", "--horizon", "200",
                   "--replicas", str(replicas)]
        previous = None
        with subprocess.Popen(command, stdout=subprocess.PIPE, text=True) as proc:
            for line in proc.stdout:
                row = json.loads(line)
                if previous is not None and previous != row["rng_initial"]:
                    raise AssertionError("RNG was reset between replicas")
                previous = row["rng_final"]
                if row["arrivals"] != row["boarded"] + row["residual"]:
                    raise AssertionError("Passenger conservation failed")
                if not math.isclose(row["queue_area"], row["wait_sum"], rel_tol=1e-8, abs_tol=1e-8):
                    raise AssertionError("Pathwise area/wait identity failed")
                for key, acc in accum.items():
                    acc[0] += 1
                    delta = row[key] - acc[1]
                    acc[1] += delta / acc[0]
                    acc[2] += delta * (row[key] - acc[1])
            if proc.wait():
                raise RuntimeError("Simulator failed")
        metrics = {}
        for key, (n, mean, m2) in accum.items():
            if n != replicas:
                raise AssertionError("Missing replicas")
            se = math.sqrt(m2 / (n - 1) / n)
            # Conservative regression envelope, not a production confidence interval.
            passed = abs(mean - expected[key]) <= 6 * se + 1e-9
            metrics[key] = {"theory": expected[key], "observed": mean,
                            "standard_error": se, "within_6se": passed}
        cases.append({"rate": rate, "headway": 10, "capacity": 10, "horizon": 200,
                      "replicas": replicas, "root_seed": 123456789,
                      "final_arrival_stream_draws": previous[0]["draws"], "metrics": metrics})
    return {"model": "controlled_finite_empty", "status": "verification_only",
            "time_unit": "consistent_arbitrary_unit", "cases": cases,
            "passed": all(m["within_6se"] for c in cases for m in c["metrics"].values()),
            "limitations": ["No empirical validation", "No network or trajectory marginal gate",
                            "Each case replays a separate verification campaign with the same root",
                            "Six-standard-error envelope is a regression diagnostic, not an acceptance CI"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=Path("build/debug/rome_bus_pmcsn.exe"))
    parser.add_argument("--replicas", type=int, default=1000)
    parser.add_argument("--output", type=Path, default=Path("reports/phase3_controlled_checks.json"))
    args = parser.parse_args()
    if args.replicas < 2:
        parser.error("At least two replicas required")
    result = verify(args.exe.resolve(), args.replicas)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
