"""Translate frozen Phase 2 JSON to the explicit PMNET1 C input format."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def export(scenario, loaded, output):
    directory = ROOT / "data/processed/phase2"
    sources = {}
    freeze = json.loads((ROOT / "reports/phase2_freeze.json").read_text(encoding="utf-8"))

    def read(name):
        data = (directory / name).read_bytes()
        sources[name] = hashlib.sha256(data).hexdigest()
        if sources[name] != freeze["generated_sha256"][name]:
            raise ValueError(f"Frozen input hash mismatch: {name}")
        return json.loads(data)

    trips = [t for t in read("trips.json") if t["window_role"] != "outside_window"]
    synthetic = read("synthetic_scenarios.json")
    initial = read("initial_states.json")
    travel = read("travel_reference.json")
    if synthetic["operational_rules"]["dwell"]["door_open_seconds"] != 2 or synthetic["operational_rules"]["dwell"]["door_close_seconds"] != 3 or synthetic["operational_rules"]["dwell"]["board_seconds_per_passenger"] != 2 or synthetic["operational_rules"]["dwell"]["alight_seconds_per_passenger"] != 1:
        raise ValueError("Unsupported operational dwell version; update the C model explicitly")
    queues = synthetic["queue_demand"]
    stops = sorted({v["stop_id"] for t in trips for v in t["visits"]})
    stop_index = {s: i for i, s in enumerate(stops)}
    queue_index = {(q["route_id"], q["direction_id"], q["stop_id"]): i for i, q in enumerate(queues)}
    fleet = {t["trip_id"]: t["capacity_passengers"] for t in synthetic["fleet_assignments"]}
    initial_bus = {b["trip_id"]: b for b in initial["initial_buses"]}
    segments = {(s["trip_id"], s["from_stop_sequence"]): s for s in travel["segments"]}
    multiplier = synthetic["scenario_multipliers"][scenario]
    lines = [f"PMNET1 25200 39600 {0 if scenario == 'REGULAR' else 0.2} {int(scenario.startswith('SHARED'))}",
             f"{len(queues)} {len(trips)}"]
    for q in queues:
        dest = [stop_index[d] for d in q["admissible_destination_stop_ids"]]
        rates = [r * multiplier for r in q["baseline_rates_passengers_per_second"]]
        lines.append(" ".join(map(str, [q["route_id"], q["direction_id"], stop_index[q["stop_id"]],
                                        len(dest), *dest, *rates])))
    passengers = []
    for bi, t in enumerate(trips):
        ib = initial_bus.get(t["trip_id"])
        first = next((i for i, v in enumerate(t["visits"]) if ib and v["stop_sequence"] == ib["next_stop_sequence"]), 0)
        time = ib["next_arrival_seconds"] if ib else t["start_seconds"]
        lines.append(" ".join(map(str, [t["route_id"], t["direction_id"], t["trip_id"], fleet[t["trip_id"]],
                                        len(t["visits"]), first, time, int(ib is None)])))
        for i, v in enumerate(t["visits"]):
            seg = segments.get((t["trip_id"], v["stop_sequence"]))
            lines.append(" ".join(map(str, [stop_index[v["stop_id"]], v["stop_sequence"], int(v["pickup_allowed"]),
                                            int(v["dropoff_allowed"]), seg["reference_travel_seconds"] if seg else 0,
                                            seg["shared_arc_id"] or "-" if seg else "-"])))
        if ib and loaded:
            for p in ib["loaded_passengers_onboard"]:
                vi = next(i for i, v in enumerate(t["visits"]) if v["stop_sequence"] == p["destination"]["stop_sequence"])
                passengers.append([1, bi, stop_index[p["destination"]["stop_id"]], vi, 25200])
    if loaded:
        for q in initial["loaded_initial_queues_by_scenario"][scenario]:
            qi = queue_index[q["route_id"], q["direction_id"], q["stop_id"]]
            for p in q["passengers"]:
                passengers.append([0, qi, stop_index[p["destination_stop_id"]], 0, p["arrival_seconds"]])
    lines.append(str(len(passengers)))
    lines.extend(" ".join(map(str, p)) for p in passengers)
    for line in lines:
        for token in line.split():
            if len(token) > 95:
                raise ValueError("Identifier exceeds C input token limit")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="ascii")
    manifest = {"schema": "PMNET1", "scenario": scenario, "initialization": "loaded_synthetic" if loaded else "empty_passengers",
                "sources": sources, "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "queues": len(queues), "trips": len(trips), "initial_passengers": len(passengers),
                "queue_index": [[q["route_id"], q["direction_id"], q["stop_id"]] for q in queues],
                "trip_index": [t["trip_id"] for t in trips], "stop_index": stops}
    output.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if not k.endswith("_index")}, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scenario", choices=["BASE", "D075", "D125", "REGULAR", "SHARED", "SHARED_D125"], default="BASE")
    p.add_argument("--loaded", action="store_true")
    p.add_argument("--output", type=Path, default=ROOT / "data/processed/phase3/network.txt")
    args = p.parse_args()
    export(args.scenario, args.loaded, args.output)
