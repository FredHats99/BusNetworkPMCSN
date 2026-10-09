"""Validate and export the selected GTFS timetable without network access."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/interim/audit-static'
sample = json.loads((ROOT / 'reports/network_sample.json').read_text(encoding='utf-8'))
selected = {r['route_id'] for r in sample['selected']}
date = sample['service_date']

def rows(name):
    with (SOURCE / name).open(encoding='utf-8-sig', newline='') as f:
        yield from csv.DictReader(f)

def seconds(value):
    h, m, s = map(int, value.split(':'))
    if h < 0 or not 0 <= m < 60 or not 0 <= s < 60:
        raise ValueError(value)
    return h * 3600 + m * 60 + s

if (SOURCE / 'calendar.txt').exists():
    raise RuntimeError('This audit uses the calendar_dates-only local snapshot.')
services = {r['service_id'] for r in rows('calendar_dates.txt')
            if r['date'] == date and r['exception_type'] == '1'}
services -= {r['service_id'] for r in rows('calendar_dates.txt')
             if r['date'] == date and r['exception_type'] == '2'}
trips = {r['trip_id']: r for r in rows('trips.txt')
         if r['route_id'] in selected and r['service_id'] in services}
stop_ids = {r['stop_id']: r for r in rows('stops.txt')}
shape_ids = {r['shape_id'] for r in rows('shapes.txt')}
times = defaultdict(list)
for r in rows('stop_times.txt'):
    if r['trip_id'] in trips:
        times[r['trip_id']].append(r)
errors = []
patterns = {}
exports = []
active_at_start = Counter()
after_end = Counter()
for tid, t in trips.items():
    records = sorted(times[tid], key=lambda r: int(r['stop_sequence']))
    if len(records) < 2:
        errors.append([tid, 'fewer_than_two_stops'])
        continue
    sequences = [int(r['stop_sequence']) for r in records]
    if len(sequences) != len(set(sequences)):
        errors.append([tid, 'duplicate_stop_sequence'])
    if t['shape_id'] not in shape_ids:
        errors.append([tid, 'missing_shape'])
    previous = -1
    for r in records:
        arrival, departure = seconds(r['arrival_time']), seconds(r['departure_time'])
        if arrival < previous or departure < arrival:
            errors.append([tid, 'nonmonotone_times', r['stop_sequence']])
        if r['stop_id'] not in stop_ids:
            errors.append([tid, 'missing_stop', r['stop_id']])
        previous = departure
    start = seconds(records[0]['departure_time'])
    end = seconds(records[-1]['arrival_time'])
    if start < 7 * 3600 < end:
        active_at_start[t['route_id']] += 1
    if 7 * 3600 <= start < 11 * 3600 and end > 11 * 3600:
        after_end[t['route_id']] += 1
    if not 7 * 3600 <= start < 11 * 3600:
        continue
    signature = tuple((r['stop_id'], r['pickup_type'], r['drop_off_type']) for r in records)
    key = (t['route_id'], t['direction_id'], signature)
    if key not in patterns:
        pattern_id = hashlib.sha256(json.dumps(key).encode()).hexdigest()[:16]
        patterns[key] = {'pattern_id': pattern_id, 'route_id': t['route_id'],
                         'direction_id': t['direction_id'], 'stop_ids': [r['stop_id'] for r in records],
                         'first_stop': stop_ids[records[0]['stop_id']]['stop_name'],
                         'last_stop': stop_ids[records[-1]['stop_id']]['stop_name'],
                         'departures': 0, 'shape_ids': set(), 'headsigns': set()}
    pattern = patterns[key]
    pattern['departures'] += 1
    pattern['shape_ids'].add(t['shape_id'])
    pattern['headsigns'].add(t['trip_headsign'])
    for r in records:
        exports.append({**{k: t[k] for k in ('route_id', 'direction_id', 'trip_id', 'service_id', 'shape_id')},
                        'pattern_id': pattern['pattern_id'],
                        **{k: r[k] for k in ('stop_id', 'stop_sequence', 'arrival_time', 'departure_time', 'pickup_type', 'drop_off_type')}})
for p in patterns.values():
    p['shape_ids'] = sorted(p['shape_ids'])
    p['headsigns'] = sorted(p['headsigns'])
hashes = {}
for name in ('routes.txt', 'trips.txt', 'stop_times.txt', 'stops.txt', 'shapes.txt', 'calendar_dates.txt', 'agency.txt'):
    with (SOURCE / name).open('rb') as f:
        hashes[name] = hashlib.file_digest(f, 'sha256').hexdigest()
result = {'service_date': date, 'source_sha256': hashes,
          'checked_active_day_trips': len(trips), 'window_departures': sum(p['departures'] for p in patterns.values()),
          'errors': errors, 'patterns': list(patterns.values()),
          'trips_in_progress_at_0700': dict(active_at_start),
          'window_trips_arriving_after_1100': dict(after_end),
          'policy': 'retain every stop/pickup/dropoff pattern and original timetable; shapes do not define patterns',
          'scope': 'structural timetable checks, not full GTFS or operational validation'}
(ROOT / 'reports/network_sample_audit.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
if errors:
    raise RuntimeError(f'{len(errors)} structural errors; inspect audit JSON before export')
output = ROOT / 'data/processed'
output.mkdir(exist_ok=True)
with (output / 'sample_timetable.csv').open('w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(exports[0]))
    writer.writeheader()
    writer.writerows(exports)
print(json.dumps({k: v for k, v in result.items() if k not in ('patterns', 'source_sha256')}, indent=2))
for p in patterns.values():
    print(p['route_id'], p['direction_id'], p['departures'], len(p['stop_ids']), p['first_stop'], '->', p['last_stop'])
