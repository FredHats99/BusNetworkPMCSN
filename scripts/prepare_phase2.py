"""Prepare traceable phase-2 GTFS inputs offline; no simulation or fitting."""
import csv
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/interim/audit-static'
OUT = ROOT / 'data/processed/phase2'
START, END, BIN = 7 * 3600, 11 * 3600, 1800


def rows(name):
    with (SOURCE / name).open(encoding='utf-8-sig', newline='') as handle:
        yield from csv.DictReader(handle)


def seconds(value):
    h, m, s = map(int, value.split(':'))
    if h < 0 or not 0 <= m < 60 or not 0 <= s < 60:
        raise ValueError(f'Invalid service time: {value}')
    return h * 3600 + m * 60 + s


def digest(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def write(name, value):
    path = OUT / name
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return digest(path)


def main():
    sample = json.loads((ROOT / 'reports/network_sample.json').read_text(encoding='utf-8'))
    selected = {item['route_id'] for item in sample['selected']}
    date = sample['service_date']
    if (SOURCE / 'calendar.txt').exists():
        raise ValueError('This snapshot adapter requires calendar_dates only.')
    services = set()
    for row in rows('calendar_dates.txt'):
        if row['date'] == date and row['exception_type'] == '1':
            services.add(row['service_id'])
    for row in rows('calendar_dates.txt'):
        if row['date'] == date and row['exception_type'] == '2':
            services.discard(row['service_id'])
    trips = {r['trip_id']: r for r in rows('trips.txt')
             if r['route_id'] in selected and r['service_id'] in services}
    times = defaultdict(list)
    for row in rows('stop_times.txt'):
        if row['trip_id'] in trips:
            times[row['trip_id']].append(row)
    patterns, exported, edges, queues = {}, [], {}, {}
    counts = Counter()
    for tid, trip in sorted(trips.items()):
        stops = sorted(times[tid], key=lambda r: int(r['stop_sequence']))
        if len(stops) < 2:
            raise ValueError(f'Incomplete trip: {tid}')
        if len({r['stop_sequence'] for r in stops}) != len(stops):
            raise ValueError(f'Duplicate sequence: {tid}')
        events = []
        for row in stops:
            pickup, dropoff = row['pickup_type'] or '0', row['drop_off_type'] or '0'
            if pickup not in ('0', '1') or dropoff not in ('0', '1'):
                raise ValueError(f'Unsupported conditional boarding/alighting: {tid}')
            event = dict(stop_id=row['stop_id'], stop_sequence=int(row['stop_sequence']),
                         arrival_seconds=seconds(row['arrival_time']),
                         departure_seconds=seconds(row['departure_time']),
                         pickup_allowed=pickup == '0', dropoff_allowed=dropoff == '0')
            if event['departure_seconds'] < event['arrival_seconds']:
                raise ValueError(f'Negative dwell: {tid}')
            if events and event['arrival_seconds'] < events[-1]['departure_seconds']:
                raise ValueError(f'Nonmonotone trip: {tid}')
            events.append(event)
        begin, finish = events[0]['departure_seconds'], events[-1]['arrival_seconds']
        signature = [(e['stop_id'], e['pickup_allowed'], e['dropoff_allowed']) for e in events]
        key = [trip['route_id'], trip['direction_id'], signature]
        pid = hashlib.sha256(json.dumps(key).encode()).hexdigest()[:16]
        if pid not in patterns:
            patterns[pid] = dict(pattern_id=pid, route_id=trip['route_id'],
                                 direction_id=trip['direction_id'], visits=signature,
                                 repeated_stop_ids=len({e['stop_id'] for e in events}) != len(events))
        active = begin < START < finish
        window = START <= begin < END
        role = 'already_in_progress' if active else 'window_departure' if window else 'outside_window'
        counts[role] += 1
        counts['window_finish_after_end'] += window and finish > END
        exported.append(dict(trip_id=tid, route_id=trip['route_id'],
                             direction_id=trip['direction_id'], pattern_id=pid,
                             shape_id=trip['shape_id'], start_seconds=begin,
                             end_seconds=finish, window_role=role, visits=events))
        for pos, event in enumerate(events):
            if event['pickup_allowed'] and role != 'outside_window':
                qkey = (trip['route_id'], trip['direction_id'], event['stop_id'])
                queue = queues.setdefault(qkey, dict(route_id=qkey[0], direction_id=qkey[1],
                                                     stop_id=qkey[2], destinations=set(), passages=set()))
                queue['destinations'].update(e['stop_id'] for e in events[pos+1:] if e['dropoff_allowed'])
                if START <= event['departure_seconds'] < END:
                    queue['passages'].add((event['departure_seconds'], tid, event['stop_sequence']))
            if pos + 1 < len(events):
                after = events[pos+1]
                arc = (event['stop_id'], after['stop_id'])
                edge = edges.setdefault(arc, dict(from_stop_id=arc[0], to_stop_id=arc[1],
                                                  route_ids=set(), programmed_gap_seconds=[]))
                edge['route_ids'].add(trip['route_id'])
                edge['programmed_gap_seconds'].append(after['arrival_seconds']-event['departure_seconds'])
    stops_used = {e['stop_id'] for t in exported for e in t['visits']}
    stop_rows = [dict(stop_id=r['stop_id'], name=r['stop_name'],
                      latitude=float(r['stop_lat']), longitude=float(r['stop_lon']))
                 for r in rows('stops.txt') if r['stop_id'] in stops_used]
    if {r['stop_id'] for r in stop_rows} != stops_used:
        raise ValueError('Missing stop metadata')
    shapes_used = {t['shape_id'] for t in exported}
    shape_points = defaultdict(list)
    for r in rows('shapes.txt'):
        if r['shape_id'] in shapes_used:
            shape_points[r['shape_id']].append([int(r['shape_pt_sequence']),
                                               float(r['shape_pt_lat']), float(r['shape_pt_lon'])])
    if set(shape_points) != shapes_used:
        raise ValueError('Missing shape')
    exported_edges = []
    for _, edge in sorted(edges.items()):
        values = edge['programmed_gap_seconds']
        exported_edges.append({**edge, 'route_ids': sorted(edge['route_ids']),
                               'sample_count': len(values), 'programmed_gap_mean_seconds': statistics.mean(values),
                               'zero_gap_count': values.count(0)})
    exported_queues = []
    for _, queue in sorted(queues.items()):
        passages = sorted(queue['passages'])
        if not queue['destinations']:
            continue
        bins = []
        for begin in range(START, END, BIN):
            stamps = [p[0] for p in passages if begin <= p[0] < begin+BIN]
            gaps = [v-u for u, v in zip(stamps, stamps[1:])]
            bins.append(dict(start_seconds=begin, end_seconds=begin+BIN, passage_count=len(stamps),
                             within_bin_headways_seconds=gaps,
                             within_bin_headway_mean_seconds=statistics.mean(gaps) if gaps else None))
        exported_queues.append({**queue, 'destinations': sorted(queue['destinations']),
                                'passages': [dict(departure_seconds=t, trip_id=tid, stop_sequence=seq)
                                             for t, tid, seq in passages], 'bins': bins})
    hashes = {name: digest(SOURCE / name) for name in
              ('routes.txt', 'trips.txt', 'stop_times.txt', 'stops.txt', 'calendar_dates.txt', 'shapes.txt')}
    OUT.mkdir(parents=True, exist_ok=True)
    outputs = {}
    for name, value in [('trips.json', exported), ('patterns.json', list(patterns.values())),
                        ('stops.json', stop_rows), ('arcs.json', exported_edges),
                        ('queues.json', exported_queues),
                        ('shapes.json', {k: sorted(v) for k, v in sorted(shape_points.items())})]:
        outputs[name] = write(name, value)
    manifest = dict(schema_version=1, source=str(SOURCE.relative_to(ROOT)).replace('\\', '/'),
                    source_sha256=hashes, service_date=date, window_seconds=[START, END],
                    demand_bin_seconds=BIN, trip_counts=dict(counts), patterns=len(patterns),
                    stops=len(stop_rows), arcs=len(exported_edges), queues=len(exported_queues),
                    repeated_stop_patterns=sum(p['repeated_stop_ids'] for p in patterns.values()),
                    window_departure_patterns=len({t['pattern_id'] for t in exported if t['window_role'] == 'window_departure'}),
                    operating_patterns=len({t['pattern_id'] for t in exported if t['window_role'] != 'outside_window'}),
                    zero_programmed_gaps=sum(e['zero_gap_count'] for e in exported_edges),
                    scheduled_dwell_nonzero=sum(e['departure_seconds'] != e['arrival_seconds']
                                                for t in exported for e in t['visits']),
                    output_sha256=outputs,
                    limitations=['programmed_not_observed_times', 'stop_pairs_not_validated_road_arcs',
                                 'od_union_requires_trip_compatibility', 'no_empirical_fit'])
    write('manifest.json', manifest)
    (ROOT / 'reports/phase2_input_manifest.json').write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in manifest.items() if k not in ('source_sha256', 'output_sha256')}, indent=2))


if __name__ == '__main__':
    main()
