"""Freeze the authorized 672-per-case confirmation using only the v1 planning data."""
from collections import defaultdict
import csv
import json
import math
from pathlib import Path
import shutil
import statistics

from gate38 import ROOT, sha, write_json, require, Accumulator
from gate38_statistics import student_critical


def plan():
    prior = ROOT / "data/processed/phase3/gate38_v1"
    old = json.loads((prior / "criteria.json").read_text())
    manifest = json.loads((prior / "manifest.json").read_text())
    require(sha(prior / "results.jsonl") == manifest["raw_sha256"]["results.jsonl"], "Prior results changed")
    require(sha(prior / "travel.csv") == manifest["raw_sha256"]["travel.csv"], "Prior travel data changed")
    for name in ("results.json", "results.md", "assertions.csv", "report_manifest.json", "software_checks.json"):
        src = ROOT / "reports" / ("gate38_"+name)
        dst = ROOT / "reports" / ("gate38_v1_"+name)
        if dst.exists():
            require(sha(src) == sha(dst), "Historical report archive already differs")
        else:
            shutil.copyfile(src, dst)
    assertions = json.loads((prior / "assertions.json").read_text())
    family = len(assertions)
    worst = max(assertions, key=lambda x: x.get("standard_error", 0)*math.sqrt(x["available_replicas"])/x["margin"])
    ratio = worst["standard_error"]*math.sqrt(worst["available_replicas"])/worst["margin"]
    n = 33
    while student_critical(n-1, .05/(2*family))*ratio/math.sqrt(n) > .5:
        n += 1
    require(n <= 672, "Authorized size no longer meets planning target")
    critical = sorted([a for a in assertions if a["status"] == "inconclusive" and a["group"].startswith("arc|")],
                      key=lambda x: abs(x.get("deviation", 0))/x["margin"], reverse=True)[:10]
    requested = {(a["case"], a["group"]) for a in critical}
    requested.update((a["other"], a["group"]) for a in critical if "other" in a)
    strata = {}
    case_ids = [c["id"] for c in manifest["cases"]]
    with (prior / "travel.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            replica = int(row["replica"])
            case = case_ids[replica//old["replicas_per_case"]]
            arc = f"arc|{row['route_id']}|{row['direction_id']}|{row['from_stop']}|{row['to_stop']}"
            if (case, arc) not in requested:
                continue
            factor, ref, duration = [float(row[k]) for k in ("factor", "reference", "duration")]
            for label in ("all", "reused" if row["reused"] == "1" else "new_key", f"bin_{row['environment_bin']}"):
                key = case, arc, label, replica
                if key not in strata:
                    strata[key] = Accumulator([])
                strata[key].add(factor, ref, duration)
    grouped = defaultdict(list)
    for (case, arc, label, replica), acc in strata.items():
        grouped[case, arc, label].append(acc.finish([]))
    targeted = []
    for (case, arc, label), rows in sorted(grouped.items()):
        targeted.append(dict(case=case, group=arc, stratum=label, available_replicas=len(rows),
                             **{k: statistics.fmean(r[k] for r in rows) for k in ("mean", "mean_reference", "mean_duration", "mean_delta", "count")}))
    paired = []
    all_stats = {(t["case"], t["group"]): t for t in targeted if t["stratum"] == "all"}
    for a in critical:
        row = {k: a[k] for k in ("case", "group", "metric", "deviation", "interval_deviation", "margin")}
        if "other" in a:
            row["other"] = a["other"]
            left, right = all_stats[a["case"], a["group"]], all_stats[a["other"], a["group"]]
            row["reference_composition_difference"] = left["mean_reference"]-right["mean_reference"]
            row["perturbation_difference"] = left["mean_delta"]-right["mean_delta"]
        paired.append(row)
    last = None
    with (prior / "results.jsonl").open() as f:
        for line in f:
            last = json.loads(line)
    final_draws = [s["draws"] for s in last["rng_final"][:4]]
    skip = 1 << max(final_draws).bit_length()
    require(skip <= 100000000, "Prefix exceeds existing batch guard")
    evidence = dict(status="planning_only_no_confirmatory_observations_used", planning_campaign=str(prior.relative_to(ROOT)),
                    prior_results_sha256=manifest["raw_sha256"]["results.jsonl"],
                    prior_assertions_sha256=sha(prior / "assertions.json"),
                    family_size=family, target_halfwidth_fraction=.5, estimated_minimum_N=n, fixed_new_N=672,
                    new_total_replicas=8064, worst_planning_assertion=worst, prior_final_stream_draws=final_draws,
                    new_prefix_draws_per_used_stream=skip, targeted_decomposition=paired, targeted_strata=targeted,
                    interpretation="Descriptive planning diagnostics; composition and factor contributions do not establish causal or statistical bias")
    write_json(ROOT / "reports/gate38_confirmation_plan.json", evidence)
    new = json.loads(json.dumps(old))
    new.update(criteria_version="1.1", status="fixed_before_independent_confirmation", purpose="confirmatory_gate_decision_not_pilot_or_production",
               replicas_per_case=672, discard_draws_each_used_stream=skip, protocol="docs/gate38_confirmation_protocol.md",
               planning_campaign=str(prior.relative_to(ROOT)).replace("\\", "/"), prior_final_stream_draws=final_draws,
               planning=dict(target_halfwidth_fraction=.5, estimated_minimum_N=n, fixed_N=672,
                             evidence_sha256=sha(ROOT / "reports/gate38_confirmation_plan.json"), planning_data_included_in_final_intervals=False))
    new["inference"]["minimum_replicas"] = 672
    new["limitations"] = [s.replace("32 replicas", "672 replicas") for s in new["limitations"]]
    new["limitations"].append("Precision planning uses estimated dispersion, not a guarantee of final half-width or equivalence; no further automatic extension")
    path = ROOT / "configs/gate38_confirmation.json"
    require(not path.exists(), "Confirmation criteria already exist; preserve the frozen version")
    write_json(path, new)
    lines = ["# Gate 3.8 — piano di conferma e diagnosi mirata", "",
             f"Solo dati diagnostici v1: {family} controlli, stima minima {n} nuove repliche per caso "
             "per semiampiezze attese entro metà margine; numerosità fissata prima della conferma: **672 per caso, 8064 totali**.", "",
             "Margini, famiglia e regole decisionali restano quelli v1. Le 384 repliche precedenti non entrano negli IC di conferma. "
             "Le stime di dispersione sono incerte; il piano non garantisce né la precisione finale né l'accettazione.", "",
             "## Scomposizione dei casi critici", "",
             "| Caso | Arco | Differenza osservata (s) | Composizione riferimenti (s) | Perturbazioni (s) |", "|---|---|---:|---:|---:|"]
    for r in paired:
        if "other" in r:
            lines.append(f"| {r['case'].replace('|', ' / ')} − {r['other'].split('|')[0]} | {r['group'].replace('|', ' / ')} | "
                         f"{r['deviation']:.6f} | {r['reference_composition_difference']:.6f} | {r['perturbation_difference']:.6f} |")
    lines.extend(["", "Il JSON conserva anche statistiche per replica separate fra chiavi nuove, riusi e bin ambientali. "
                  "Le celle con osservazioni assenti non sono imputate a zero; sono statistiche descrittive, senza decisioni aggiuntive sui margini.", "",
                  f"Consumi finali v1 degli stream 0–3: `{final_draws}`. Prefisso della conferma: `{skip}` per ciascuno stream, "
                  "strettamente oltre tutti gli estremi precedenti. La conferma continua gli stati fra tutti i casi.", "",
                  "Una differenza di perturbazione osservata non distingue da sola fluttuazione Monte Carlo e selezione endogena. "
                  "La nuova campagna indipendente è l'evidenza decisiva secondo il protocollo congelato."])
    (ROOT / "reports/gate38_confirmation_plan.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(json.dumps({k: evidence[k] for k in ("estimated_minimum_N", "fixed_new_N", "new_total_replicas", "prior_final_stream_draws", "new_prefix_draws_per_used_stream")}, indent=2))


if __name__ == "__main__":
    plan()
