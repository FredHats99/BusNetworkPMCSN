"""Fixed-size gate 3.8 campaign and replica-level input diagnostics (stdlib).

Run: python scripts/gate38.py
Reanalyse retained raw files: python scripts/gate38.py --analyze-only RUN_DIRECTORY
No adaptive extension, threshold tuning or production estimates.
"""
import argparse
from array import array
from collections import Counter
import contextlib
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time

from export_simulation import export, ROOT
from gate38_statistics import assess


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def arc_key(route, direction, start, end):
    return f"arc|{route}|{direction}|{start}|{end}"


def input_structure(manifest):
    directory = ROOT / "data/processed/phase2"
    trips = {t["trip_id"]: t for t in json.loads((directory / "trips.json").read_text())}
    reference = json.loads((directory / "travel_reference.json").read_text())
    segments = {(s["trip_id"], s["from_stop_sequence"]): s for s in reference["segments"]}
    initials = {b["trip_id"]: b for b in json.loads((directory / "initial_states.json").read_text())["initial_buses"]}
    stops = {s: i for i, s in enumerate(manifest["stop_index"])}
    expected = {}
    nominal_arcs = set()
    lines = set()
    for bi, trip_id in enumerate(manifest["trip_index"]):
        trip = trips[trip_id]
        route, direction = trip["route_id"], trip["direction_id"]
        lines.add(f"line|{route}|{direction}")
        first = initials.get(trip_id, {}).get("next_stop_sequence", trip["visits"][0]["stop_sequence"])
        for index, (v, nxt) in enumerate(zip(trip["visits"], trip["visits"][1:])):
            if v["stop_sequence"] < first:
                continue
            segment = segments[trip_id, v["stop_sequence"]]
            start, end = stops[v["stop_id"]], stops[nxt["stop_id"]]
            arc = arc_key(route, direction, start, end)
            expected[bi, v["stop_sequence"]] = dict(route=route, direction=direction, trip=trip_id,
                start=start, end=end, next_sequence=nxt["stop_sequence"], reference=segment["reference_travel_seconds"],
                shared=segment["shared_arc_id"] or "-", arc=arc, from_index=index)
            if v["departure_seconds"] < 39600:
                nominal_arcs.add(arc)
    return expected, sorted(nominal_arcs), ["network", *sorted(lines), "domain|inside", "domain|outside"]


def inventory(criteria, cases, arcs, broad_groups):
    margins = criteria["margins"]
    factor_metrics = [("mean", 1.0, margins["factor_mean_absolute"]),
                      ("cv", .2, margins["factor_cv_absolute"])]
    factor_metrics += [(f"cdf_{p:g}", p, margins["cdf_probability_absolute"]) for p in criteria["cdf_probabilities"]]
    assertions = []
    for case in cases:
        if case["scenario"] != "REGULAR":
            for group in broad_groups:
                for metric, target, margin in factor_metrics:
                    assertions.append(dict(kind="reference_marginal", case=case["id"], group=group,
                                           metric=metric, target=target, margin=margin))
        for arc in arcs:
            assertions.append(dict(kind="reference_arc_time", case=case["id"], group=arc,
                                   metric="mean_delta", target=0, margin=margins["arc_travel_mean_seconds"]))
    for mode in criteria["initializations"]:
        for a, b in criteria["comparisons"]:
            for arc in arcs:
                assertions.append(dict(kind="comparison_arc_time", case=f"{a}|{mode}", other=f"{b}|{mode}",
                                       group=arc, metric="mean_duration", target=0, margin=margins["arc_travel_mean_seconds"]))
        for a, b in criteria["stochastic_comparisons"]:
            for group in broad_groups:
                for metric, _, margin in factor_metrics:
                    assertions.append(dict(kind="comparison_marginal", case=f"{a}|{mode}", other=f"{b}|{mode}",
                                           group=group, metric=metric, target=0, margin=margin))
    return assertions


class Accumulator:
    __slots__ = ("n", "total", "square", "ref", "duration", "cdf", "thresholds")

    def __init__(self, thresholds):
        self.n = 0
        self.total = self.square = self.ref = self.duration = 0.0
        self.cdf = [0]*len(thresholds)
        self.thresholds = thresholds

    def add(self, factor, reference, duration):
        self.n += 1
        self.total += factor
        self.square += factor*factor
        self.ref += reference
        self.duration += duration
        for i, threshold in enumerate(self.thresholds):
            if factor <= threshold:
                self.cdf[i] += 1

    def finish(self, probabilities):
        mean = self.total/self.n
        result = dict(count=self.n, mean=mean,
                      cv=math.sqrt(max(0, self.square/self.n-mean*mean))/mean if self.n >= 2 else None,
                      mean_duration=self.duration/self.n, mean_reference=self.ref/self.n,
                      mean_delta=(self.duration-self.ref)/self.n)
        result.update({f"cdf_{p:g}": self.cdf[i]/self.n for i, p in enumerate(probabilities)})
        return result


def prepare(args):
    criteria_path = args.criteria.resolve()
    criteria = json.loads(criteria_path.read_text())
    require(criteria["root_seed"] == 123456789, "C diagnostic batch root differs from criteria")
    require(criteria["replicas_per_case"] >= criteria["inference"]["minimum_replicas"], "Insufficient planned replicas")
    directory = args.output_dir.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(criteria_path, directory / "criteria.json")
    cases = []
    with (directory / "exports.log").open("w") as log, contextlib.redirect_stdout(log):
        for scenario in criteria["scenarios"]:
            for mode in criteria["initializations"]:
                path = directory / f"{scenario}_{mode}.txt"
                export(scenario, mode == "loaded_synthetic", path)
                cases.append(dict(id=f"{scenario}|{mode}", scenario=scenario, initialization=mode,
                                  input=str(path), input_sha256=sha(path), manifest=str(path.with_suffix(".manifest.json")),
                                  manifest_sha256=sha(path.with_suffix(".manifest.json"))))
    sidecar = json.loads(Path(cases[0]["manifest"]).read_text())
    _, arcs, broad_groups = input_structure(sidecar)
    checks = inventory(criteria, cases, arcs, broad_groups)
    write_json(directory / "assertion_inventory.json", checks)
    plan = directory / "campaign.txt"
    plan.write_text(f"PMDIAG1 {len(cases)} {criteria['replicas_per_case']} {criteria['discard_draws_each_used_stream']}\n" +
                    "\n".join(c["input"] for c in cases) + "\n", encoding="ascii")
    sources = [*sorted((ROOT / "src/simulation").glob("*.c")), ROOT / "include/rome_bus_pmcsn/simulation.h",
               ROOT / "scripts/gate38.py", ROOT / "scripts/gate38_statistics.py", ROOT / "scripts/export_simulation.py",
               ROOT / criteria.get("protocol", "docs/gate38_protocol.md")]
    manifest = dict(criteria_sha256=sha(criteria_path), criteria_source=str(criteria_path.relative_to(ROOT)),
                    inventory_sha256=sha(directory / "assertion_inventory.json"),
                    executable=str(args.exe.resolve()), exe_sha256=sha(args.exe), cases=cases,
                    arc_groups=arcs, broad_groups=broad_groups, assertion_count=len(checks),
                    source_sha256={str(p.relative_to(ROOT)): sha(p) for p in sources}, status="prepared_before_run")
    write_json(directory / "manifest.json", manifest)
    if "planning_campaign" in criteria:
        prior = ROOT / criteria["planning_campaign"]
        prior_manifest = json.loads((prior / "manifest.json").read_text())
        require(sha(prior / "results.jsonl") == prior_manifest["raw_sha256"]["results.jsonl"], "Planning results changed")
        require(sha(directory / "assertion_inventory.json") == prior_manifest["inventory_sha256"], "Confirmatory assertion inventory differs")
        last = None
        with (prior / "results.jsonl").open() as f:
            for line in f:
                last = json.loads(line)
        draws = [s["draws"] for s in last["rng_final"][:4]]
        require(draws == criteria["prior_final_stream_draws"], "Planning RNG endpoint changed")
        require(all(d < criteria["discard_draws_each_used_stream"] for d in draws), "New random-number range overlaps planning")
        manifest["planning_evidence"] = dict(directory=str(prior), results_sha256=sha(prior / "results.jsonl"),
                                             final_used_stream_draws=draws, inventory_sha256=prior_manifest["inventory_sha256"])
        write_json(directory / "manifest.json", manifest)
    cache = args.exe.resolve().parent / "CMakeCache.txt"
    ctest = shutil.which("ctest")
    if not ctest and cache.exists():
        for line in cache.read_text().splitlines():
            if line.startswith("CMAKE_CTEST_COMMAND:INTERNAL="):
                ctest = line.split("=", 1)[1]
    require(ctest, "Cannot locate CTest; build the project first")
    commands = [[ctest, "--test-dir", str(args.exe.resolve().parent), "--output-on-failure"],
                [sys.executable, str(ROOT / "tests/test_gate38_statistics.py")],
                [sys.executable, str(ROOT / "tests/test_gate38_analysis.py")],
                [sys.executable, str(ROOT / "tests/test_gate38_travel.py"), "--exe", str(args.exe.resolve())]]
    with (directory / "software_tests.log").open("w") as log:
        for command in commands:
            completed = subprocess.run(command, stdout=log, stderr=log)
            require(completed.returncode == 0, f"Software prerequisite failed: {command}")
    manifest["software_tests"] = dict(status="passed", log_sha256=sha(directory / "software_tests.log"))
    manifest["status"] = "running"
    write_json(directory / "manifest.json", manifest)
    started = time.perf_counter()
    with (directory / "results.jsonl").open("w") as out, (directory / "progress.log").open("w") as progress:
        completed = subprocess.run([str(args.exe.resolve()), "diagnose", "network", str(plan), "--travel-trace", str(directory / "travel.csv")],
                                   stdout=out, stderr=progress)
    manifest["elapsed_seconds"] = time.perf_counter()-started
    manifest["returncode"] = completed.returncode
    manifest["status"] = "collected" if completed.returncode == 0 else "collection_failed"
    manifest["raw_sha256"] = {name: sha(directory / name) for name in ("results.jsonl", "travel.csv", "progress.log") if (directory / name).exists()}
    write_json(directory / "manifest.json", manifest)
    require(completed.returncode == 0, "Diagnostic collection failed; raw files retained, gate not accepted")
    return directory


def collect(directory, criteria, manifest):
    require(manifest.get("returncode") == 0, "No complete successful campaign")
    require(sha(directory / "criteria.json") == manifest["criteria_sha256"], "Criteria changed after preregistration")
    require(sha(directory / "assertion_inventory.json") == manifest["inventory_sha256"], "Assertion inventory changed")
    for name, digest in manifest["raw_sha256"].items():
        require(sha(directory / name) == digest, f"Raw file changed: {name}")
    cases = manifest["cases"]
    replicas = criteria["replicas_per_case"]
    skip = criteria["discard_draws_each_used_stream"]
    summaries = []
    previous_final = None
    with (directory / "results.jsonl").open() as f:
        for i, line in enumerate(f):
            result = json.loads(line)
            require(result["replica"] == i and result["root_seed"] == criteria["root_seed"], "Replica/root mismatch")
            require(result["arrivals"] == result["boarded"]+result["unserved"], "Passenger balance")
            require(result["rng_final"][1]["draws"]-result["rng_initial"][1]["draws"] == result["arrivals"], "Destination draw accounting")
            require(result["rng_final"][0]["draws"]-result["rng_initial"][0]["draws"] == result["arrivals"]+len(result["queues"]), "Arrival draw accounting for frozen positive-rate queues")
            require(math.isclose(result["queue_area"], result["restricted_wait_sum"], rel_tol=1e-7, abs_tol=1e-7), "Area/wait identity")
            if previous_final is not None:
                require(result["rng_initial"] == previous_final, "RNG reset at replica/case boundary")
            else:
                require([s["draws"] for s in result["rng_initial"][:4]] == [skip]*4, "Diagnostic prefix not discarded")
            previous_final = result["rng_final"]
            summaries.append(dict(environment_keys=result["environment_keys"], visits=tuple(b["visit"] for b in result["buses"]),
                                  travel_draws=[result["rng_final"][s]["draws"]-result["rng_initial"][s]["draws"] for s in (2, 3)]))
    require(len(summaries) == replicas*len(cases), "Missing/extra replica summaries")
    require(manifest["software_tests"]["status"] == "passed", "Software tests missing")
    require(sha(directory / "software_tests.log") == manifest["software_tests"]["log_sha256"], "Software-test log changed")
    by_case = {c["id"]: c for c in cases}
    for c in cases:
        require(sha(c["input"]) == c["input_sha256"], "Campaign input changed")
        require(sha(c["manifest"]) == c["manifest_sha256"], "Campaign sidecar changed")
    for mode in criteria["initializations"]:
        for a, b in criteria["comparisons"]:
            pa, pb = Path(by_case[f"{a}|{mode}"]["input"]), Path(by_case[f"{b}|{mode}"]["input"])
            require(pa.read_text().splitlines()[1:] == pb.read_text().splitlines()[1:], f"Common parameters differ: {a}/{b}/{mode}")
    sidecar = json.loads(Path(cases[0]["manifest"]).read_text())
    for name, digest in sidecar["sources"].items():
        require(sha(ROOT / "data/processed/phase2" / name) == digest, "Phase 2 source changed")
    expected, arcs, broad = input_structure(sidecar)
    require(arcs == manifest["arc_groups"] and broad == manifest["broad_groups"], "Input group inventory changed")
    probabilities = criteria["cdf_probabilities"]
    sigma2 = math.log1p(.2*.2)
    thresholds = [math.exp(-sigma2/2+math.sqrt(sigma2)*statistics.NormalDist().inv_cdf(p)) for p in probabilities]
    data = {c["id"]: {} for c in cases}
    diagnostics = []
    current = -1
    groups = {}
    cache = {}
    seen = set()
    previous_departure = -math.inf
    group_stats_file = (directory / "replica_statistics.jsonl").open("w")

    def finish():
        if current < 0:
            return
        case = cases[current//replicas]
        local = current % replicas
        result = summaries[current]
        new = len(cache)
        regular = case["scenario"] == "REGULAR"
        stream = 3 if case["scenario"].startswith("SHARED") else 2
        for s in (2, 3):
            draws = result["travel_draws"][s-2]
            require(draws == (2*new if s == stream and not regular else 0), f"Travel RNG accounting replica {current}")
        require(new == result["environment_keys"], "Missing environment factor records")
        expected_seen = {key for key, info in expected.items() if info["from_index"] < result["visits"][key[0]]}
        require(seen == expected_seen, "Missing/extra traversal records relative to terminal bus states")
        require(bool(seen), "No segment records in replica")
        finished = {g: a.finish(probabilities) for g, a in groups.items()}
        for g, stats in finished.items():
            columns = data[case["id"]].setdefault(g, {})
            for metric, value in stats.items():
                if metric not in columns:
                    columns[metric] = array("d", [math.nan])*replicas
                columns[metric][local] = math.nan if value is None else value
        group_stats_file.write(json.dumps(dict(replica=current, case=case["id"], groups=finished), allow_nan=False)+"\n")
        count = finished["network"]["count"]
        diagnostics.append(dict(replica=current, case=case["id"], traversals=count, unique_keys=new,
                                reuse_fraction=0 if regular else 1-new/count,
                                unfinished_traversals=unfinished,
                                arcs_outside_nominal_inventory=sorted({k for k in finished if k.startswith("arc|")}-set(arcs))))

    try:
        with (directory / "travel.csv").open(newline="") as f:
            for row in csv.DictReader(f):
                replica = int(row["replica"])
                if replica != current:
                    require(replica == current+1 and replica < len(summaries), "Out-of-order/missing travel replica")
                    finish()
                    current = replica; groups = {}; cache = {}; seen = set(); unfinished = 0; previous_departure = -math.inf
                case = cases[current//replicas]
                regular = case["scenario"] == "REGULAR"
                shared = int(case["scenario"].startswith("SHARED"))
                bus, sequence = int(row["bus"]), int(row["from_sequence"])
                require((bus, sequence) not in seen, "Duplicate segment traversal")
                seen.add((bus, sequence))
                exp = expected.get((bus, sequence))
                require(exp is not None, "Unexpected trip/segment, including initial residual")
                require((row["route_id"], row["direction_id"], row["trip_id"], int(row["from_stop"]), int(row["to_stop"]), int(row["to_sequence"]), row["shared_arc"]) ==
                        (exp["route"], exp["direction"], exp["trip"], exp["start"], exp["end"], exp["next_sequence"], exp["shared"]), "Geometry/identifier mismatch")
                departure, arrival, ref, duration, factor = [float(row[k]) for k in ("departure", "arrival", "reference", "duration", "factor")]
                require(all(math.isfinite(x) for x in (departure, arrival, ref, duration, factor)) and min(ref, duration, factor) > 0, "Nonpositive/nonfinite travel")
                require(25200 <= departure < 39600 and departure >= previous_departure, "Travel window/order mismatch")
                previous_departure = departure
                require(ref == exp["reference"] and math.isclose(duration, ref*factor, rel_tol=2e-14) and math.isclose(arrival, departure+duration, abs_tol=1e-9), "Duration/decomposition mismatch")
                require(int(row["environment_bin"]) == math.floor(departure/300), "Wrong environment bin")
                require(int(row["shared_mode"]) == shared and float(row["cv"]) == (0 if regular else .2), "Wrong scenario travel parameters")
                completes = int(arrival < 39600)
                require(int(row["completes_before_end"]) == completes, "Wrong terminal censoring flag")
                unfinished += 1-completes
                new = not int(row["reused"])
                if regular:
                    require(factor == 1 and duration == ref and row["environment_key"] == "" and int(row["factor_index"]) == -1 and new, "REGULAR has stochastic state")
                else:
                    key = f"|{exp['shared']}" if shared and exp["shared"] != "-" else f"{exp['route']}|{exp['shared']}" if exp["shared"] != "-" else f"{exp['route']}|{exp['start']}|{exp['end']}"
                    require(row["environment_key"] == key, "Incorrect canonical environment key")
                    cache_key = key, int(row["environment_bin"])
                    index = int(row["factor_index"])
                    if cache_key in cache:
                        require(not new and cache[cache_key] == (index, factor), "Factor was resampled or reuse not recorded")
                    else:
                        require(new and index == len(cache), "Missing/duplicate new key or factor index")
                        cache[cache_key] = index, factor
                selected_groups = ["network", f"line|{exp['route']}|{exp['direction']}",
                                   "domain|inside" if exp["shared"] != "-" else "domain|outside", exp["arc"],
                                   f"bin|{int(row['environment_bin'])}"]
                if new and not regular:
                    selected_groups.append("new_keys_only")
                for g in selected_groups:
                    if g not in groups:
                        groups[g] = Accumulator(thresholds)
                    groups[g].add(factor, ref, duration)
        finish()
    finally:
        group_stats_file.close()
    require(current == len(summaries)-1, "Final travel replicas missing")
    return data, diagnostics


def analyse(directory):
    criteria = json.loads((directory / "criteria.json").read_text())
    manifest = json.loads((directory / "manifest.json").read_text())
    data, diagnostics = collect(directory, criteria, manifest)
    checks = json.loads((directory / "assertion_inventory.json").read_text())
    family_size = len(checks)
    n = criteria["replicas_per_case"]
    outcomes = []
    for spec in checks:
        values = data[spec["case"]].get(spec["group"], {}).get(spec["metric"], [None]*n)
        if "other" in spec:
            other_values = data[spec["other"]].get(spec["group"], {}).get(spec["metric"], [None]*n)
            values = [a-b if a is not None and b is not None else None for a, b in zip(values, other_values)]
        outcome = assess(values, spec["target"], spec["margin"], family_size,
                         criteria["inference"]["family_confidence"], n)
        outcomes.append({**spec, **outcome})
    counts = Counter(x["status"] for x in outcomes)
    status = "accepted" if counts["passed"] == len(outcomes) else "failed" if counts["failed"] else "inconclusive"
    by_kind = {kind: dict(Counter(x["status"] for x in outcomes if x["kind"] == kind)) for kind in sorted({x["kind"] for x in outcomes})}
    broad = [x for x in outcomes if x["group"] in manifest["broad_groups"]]
    worst = sorted([x for x in outcomes if x["status"] != "passed"],
                   key=lambda x: abs(x.get("deviation", 0))/x["margin"], reverse=True)[:30]
    report = dict(gate="3.8", criteria_version=criteria["criteria_version"], status=status,
                  exact_requirements="passed", software_tests=manifest["software_tests"],
                  criteria_sha256=manifest["criteria_sha256"], inventory_sha256=manifest["inventory_sha256"],
                  collection_exe_sha256=manifest["exe_sha256"], collection_source_sha256=manifest["source_sha256"],
                  analysis_source_sha256={str(p.relative_to(ROOT)): sha(p) for p in (ROOT / "scripts/gate38.py", ROOT / "scripts/gate38_statistics.py")},
                  run_directory=str(directory), replicas=n*len(manifest["cases"]), family_size=family_size,
                  nominal_simultaneous_confidence=criteria["inference"]["family_confidence"],
                  assertion_counts=dict(counts), by_kind=by_kind, broad_group_assertions=broad, blockers_sample=worst,
                  elapsed_collection_seconds=manifest["elapsed_seconds"],
                  limitations=criteria["limitations"], assertions_file=str(directory / "assertions.json"),
                  diagnostics_file=str(directory / "diagnostics.json"))
    if "planning_campaign" in criteria:
        report["confirmation"] = dict(planning_campaign=criteria["planning_campaign"], planning_data_included=False,
                                      target_halfwidth_fraction=criteria["planning"]["target_halfwidth_fraction"],
                                      precision_targets_met=sum((x.get("interval_deviation", [0, math.inf])[1]-x.get("interval_deviation", [0, math.inf])[0])/2 <= x["margin"]*criteria["planning"]["target_halfwidth_fraction"] for x in outcomes),
                                      precision_targets_total=len(outcomes))
    write_json(directory / "assertions.json", outcomes)
    write_json(directory / "diagnostics.json", diagnostics)
    write_json(directory / "gate38_results.json", report)
    write_json(ROOT / "reports/gate38_results.json", report)
    lines = ["# Gate 3.8 — esito diagnostico", "", f"Esito: **{status}**. Requisiti esatti: superati.", "",
             f"Campagna: {report['replicas']} repliche; {family_size} asserti obbligatori; IC Student Bonferroni simultanei nominali al 95%.", "",
             "| Famiglia | Superati | Non superati | Inconcludenti |", "|---|---:|---:|---:|"]
    for kind, count in by_kind.items():
        lines.append(f"| {kind} | {count.get('passed', 0)} | {count.get('failed', 0)} | {count.get('inconclusive', 0)} |")
    lines.extend(["", "Ogni asserto obbligatorio non superato o inconcludente impedisce l'accettazione completa.",
                  "Le tolleranze e la numerosità non sono state modificate sulla base dei risultati.", "",
                  f"Criteri SHA256: `{report['criteria_sha256']}`.",
                  f"Dati e asserti completi: `{directory.relative_to(ROOT) if directory.is_relative_to(ROOT) else directory}`.", "",
                  "Nessuna validazione empirica di domanda/OD/tempi reali; nessun pilota o produzione.",
                  "La copertura Student è approssimata per statistiche di replica non normali; la griglia CDF non copre le code estreme."])
    (ROOT / "reports/gate38_results.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    from render_gate38_report import render
    render(directory, verbose=False)
    print(json.dumps({k: report[k] for k in ("status", "replicas", "family_size", "assertion_counts", "by_kind")}, indent=2))
    return status


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=ROOT / "build/debug/rome_bus_pmcsn.exe")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/processed/phase3/gate38_v1")
    parser.add_argument("--criteria", type=Path, default=ROOT / "configs/gate38_criteria.json")
    parser.add_argument("--analyze-only", type=Path)
    args = parser.parse_args()
    run_directory = args.analyze_only.resolve() if args.analyze_only else prepare(args)
    try:
        outcome = analyse(run_directory)
    except Exception as error:
        invalid = dict(gate="3.8", status="invalid", exact_requirements="failed", run_directory=str(run_directory),
                       error=f"{type(error).__name__}: {error}")
        write_json(run_directory / "gate38_error.json", invalid)
        write_json(ROOT / "reports/gate38_results.json", invalid)
        (ROOT / "reports/gate38_results.md").write_text(
            "# Gate 3.8 — analisi non valida\n\nControlli esatti non superati. Nessuna accettazione.\n\n" + invalid["error"] + "\n", encoding="utf-8")
        print(json.dumps(invalid, indent=2), file=sys.stderr)
        raise SystemExit(1)
    # 0 accepted, 2 completed but failed equivalence, 3 completed but inconclusive.
    raise SystemExit({"accepted": 0, "failed": 2, "inconclusive": 3}[outcome])
