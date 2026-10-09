"""Offline GTFS sample selection; analysis helper, not simulation code."""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/interim/audit-static'
DATE = '20261012'

def rows(name):
    with (SOURCE / name).open(encoding='utf-8-sig', newline='') as f:
        yield from csv.DictReader(f)

def seconds(value):
    h, m, s = map(int, value.split(':'))
    return h * 3600 + m * 60 + s

routes = {r['route_id']: r for r in rows('routes.txt') if r['route_type'] == '3'}
services = {r['service_id'] for r in rows('calendar_dates.txt')
            if r['date'] == DATE and r['exception_type'] == '1'}
services -= {r['service_id'] for r in rows('calendar_dates.txt')
             if r['date'] == DATE and r['exception_type'] == '2'}
trips = {r['trip_id']: r for r in rows('trips.txt')
         if r['route_id'] in routes and r['service_id'] in services}
starts = {}
trip_stops = defaultdict(set)
trip_sequences = defaultdict(list)
for r in rows('stop_times.txt'):
    tid = r['trip_id']
    if tid not in trips:
        continue
    seq = int(r['stop_sequence'])
    if tid not in starts or seq < starts[tid][0]:
        starts[tid] = (seq, seconds(r['departure_time']))
    trip_stops[tid].add(r['stop_id'])
    trip_sequences[tid].append((seq, r['stop_id']))
counts = Counter()
directions = defaultdict(Counter)
stops = defaultdict(set)
shapes = defaultdict(set)
arcs = defaultdict(set)
for tid, (_, departure) in starts.items():
    if not 7 * 3600 <= departure < 11 * 3600:
        continue
    t = trips[tid]
    rid = t['route_id']
    counts[rid] += 1
    directions[rid][t['direction_id']] += 1
    stops[rid].update(trip_stops[tid])
    shapes[rid].add(t['shape_id'])
    sequence = [sid for _, sid in sorted(trip_sequences[tid])]
    arcs[rid].update(zip(sequence, sequence[1:]))
# Require both directions and at least two departures/hour in each direction.
candidates = [rid for rid in counts if directions[rid]['0'] >= 8
              and directions[rid]['1'] >= 8]
selected = []
replacement_ids = {'2BUS', '3NAV', '5BUS', '14BUS', '19BUS'}
# Ordinary numeric bus labels form the initial pool; special labels are excluded.
# 3NAV is excluded because the snapshot differs from the temporary terminus notice.
ordinary = [rid for rid in candidates if routes[rid]['route_short_name'].isdigit()]
replacement = [rid for rid in candidates if rid in replacement_ids and rid != '3NAV']
selection_steps = []
while len(selected) < 6:
    pool = ordinary if len(selected) < 4 else replacement
    eligible = [rid for rid in pool if rid not in selected
                and (not selected or any(arcs[rid] & arcs[s] for s in selected))]
    if not selected:
        # Anchor the ordinary core where two replacement services can connect.
        eligible = [rid for rid in eligible
                    if sum(bool(arcs[rid] & arcs[r]) for r in replacement) >= 2]
    if not eligible:
        raise RuntimeError('Cannot meet four ordinary/two replacement connected route quota')
    union = set().union(*(arcs[s] for s in selected)) if selected else set()
    # Frequency and directed consecutive shared stop pairs; ties use route_id.
    best = min(eligible, key=lambda rid: (
        -(counts[rid] / max(counts[r] for r in ordinary) + min(len(arcs[rid] & union), 20) / 20), rid))
    selection_steps.append({'route_id': best, 'class': 'ordinary_numeric_label' if best in ordinary else 'tram_replacement',
                            'shared_directed_stop_pairs_with_previous': len(arcs[best] & union),
                            'score': counts[best] / max(counts[r] for r in ordinary) + min(len(arcs[best] & union), 20) / 20})
    selected.append(best)
result = {
    'source': str(SOURCE.relative_to(ROOT)), 'service_date': DATE,
    'departure_window': '[07:00,11:00)', 'route_type': 3,
    'calendar_policy': 'calendar_dates only; source has no calendar.txt',
    'criterion': 'four ordinary numeric-label routes then two tram replacements; ordinary seed adjacent to at least two replacements; greedy frequency + shared directed consecutive stop pairs',
    'score_formula': 'departures/max_ordinary_departures + min(shared_directed_stop_pairs_with_selected_union,20)/20; ties by route_id',
    'selection_steps': selection_steps,
    'excluded_known_topology_mismatch': ['3NAV'],
    'eligible_routes': len(candidates),
    'selected': [{'route_id': rid, 'name': routes[rid]['route_short_name'],
                  'agency_id': routes[rid]['agency_id'], 'departures': counts[rid],
                  'departures_by_direction': dict(directions[rid]),
                  'stop_ids_count': len(stops[rid]), 'shape_ids_count': len(shapes[rid])}
                 for rid in selected],
    'shared_stop_ids': [{'routes': [a, b], 'count': len(stops[a] & stops[b])}
                        for i, a in enumerate(selected) for b in selected[i+1:]],
    'shared_directed_stop_pairs': [{'routes': [a, b], 'count': len(arcs[a] & arcs[b])}
                                  for i, a in enumerate(selected) for b in selected[i+1:]],
    'total_unique_stop_ids': len(set().union(*(stops[rid] for rid in selected))),
    'total_departures': sum(counts[rid] for rid in selected),
}
output = ROOT / 'reports/network_sample.json'
output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2, ensure_ascii=False))
