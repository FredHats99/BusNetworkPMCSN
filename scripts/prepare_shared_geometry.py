"""Conservative, reproducible shared-segment check on the archived GTFS shapes."""
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/processed/phase2'
ANCHOR_LIMIT_M, MATCH_LIMIT_M, LENGTH_RATIO_LIMIT = 60.0, 25.0, 1.10
SAMPLES = 101


def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


def xy(latitude, longitude):
    # Local equirectangular metric for the Rome snapshot, not a routing engine.
    radius = 6371000.0
    return (radius*math.radians(longitude)*math.cos(math.radians(42)),
            radius*math.radians(latitude))


def distance(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])


def anchors(polyline, stop_points):
    cumulative = [0.0]
    for a, b in zip(polyline, polyline[1:]):
        cumulative.append(cumulative[-1]+distance(a, b))
    previous, result = 0.0, []
    for point in stop_points:
        best = None
        for j, (a, b) in enumerate(zip(polyline, polyline[1:])):
            length = cumulative[j+1]-cumulative[j]
            if length == 0 or cumulative[j+1] < previous:
                continue
            fraction = ((point[0]-a[0])*(b[0]-a[0])+(point[1]-a[1])*(b[1]-a[1]))/(length*length)
            fraction = min(1.0, max(0.0, fraction, (previous-cumulative[j])/length))
            projected = (a[0]+fraction*(b[0]-a[0]), a[1]+fraction*(b[1]-a[1]))
            candidate = (distance(point, projected), cumulative[j]+fraction*length)
            if best is None or candidate < best:
                best = candidate
        if best is None:
            raise ValueError('No monotone shape projection')
        error, previous = best
        result.append((previous, error))
    return cumulative, result


def sample_segment(polyline, cumulative, begin, end):
    points, index = [], 0
    for n in range(SAMPLES):
        target = begin+(end-begin)*n/(SAMPLES-1)
        while index+1 < len(cumulative)-1 and cumulative[index+1] < target:
            index += 1
        length = cumulative[index+1]-cumulative[index]
        fraction = (target-cumulative[index])/length if length else 0
        a, b = polyline[index], polyline[index+1]
        points.append((a[0]+fraction*(b[0]-a[0]), a[1]+fraction*(b[1]-a[1])))
    return points


def equivalent(a, b):
    return (max(a['length_m'], b['length_m'])/min(a['length_m'], b['length_m']) <= LENGTH_RATIO_LIMIT
            and max(distance(x, y) for x, y in zip(a['samples'], b['samples'])) <= MATCH_LIMIT_M)


def main():
    trips = [t for t in read('trips.json') if t['window_role'] != 'outside_window']
    stops = {s['stop_id']: xy(s['latitude'], s['longitude']) for s in read('stops.json')}
    shapes = {sid: [xy(lat, lon) for _, lat, lon in points] for sid, points in read('shapes.json').items()}
    unique = {}
    for trip in trips:
        key = (trip['route_id'], trip['shape_id'], tuple(v['stop_id'] for v in trip['visits']))
        unique.setdefault(key, trip)
    variants, by_pair, rejections = {}, defaultdict(list), []
    for key, trip in sorted(unique.items()):
        polyline = shapes[trip['shape_id']]
        cumulative, projected = anchors(polyline, [stops[v['stop_id']] for v in trip['visits']])
        for i, (a, b) in enumerate(zip(trip['visits'], trip['visits'][1:])):
            identity = (trip['route_id'], trip['shape_id'], a['stop_id'], b['stop_id'])
            if identity in variants:
                continue
            begin, error_a = projected[i]
            end, error_b = projected[i+1]
            if max(error_a, error_b) > ANCHOR_LIMIT_M or end-begin <= 1:
                rejections.append(dict(key=identity, reason='anchor_distance_or_nonpositive_projected_length',
                                       max_anchor_error_m=max(error_a, error_b), length_m=end-begin))
                variants[identity] = None
                continue
            segment = dict(identity=identity, length_m=end-begin, anchor_error_m=max(error_a, error_b),
                           samples=sample_segment(polyline, cumulative, begin, end))
            variants[identity] = segment
            by_pair[(a['stop_id'], b['stop_id'])].append(segment)
    groups, identity_to_group = [], {}
    for pair, segments in sorted(by_pair.items()):
        clusters = []
        for segment in sorted(segments, key=lambda s: s['identity']):
            for cluster in clusters:
                if all(equivalent(segment, other) for other in cluster):
                    cluster.append(segment)
                    break
            else:
                clusters.append([segment])
        for cluster in clusters:
            routes = sorted({s['identity'][0] for s in cluster})
            if len(routes) < 2:
                continue
            members = [s['identity'] for s in cluster]
            gid = hashlib.sha256(json.dumps(members).encode()).hexdigest()[:16]
            max_deviation = max(distance(x, y) for a in cluster for b in cluster for x, y in zip(a['samples'], b['samples']))
            groups.append(dict(shared_arc_id=gid, from_stop_id=pair[0], to_stop_id=pair[1], route_ids=routes,
                               members=members, max_sampled_deviation_m=max_deviation,
                               maximum_anchor_error_m=max(s['anchor_error_m'] for s in cluster),
                               max_length_ratio=max(s['length_m'] for s in cluster)/min(s['length_m'] for s in cluster)))
            for member in members:
                identity_to_group[member] = gid
    mapping = []
    for trip in sorted(trips, key=lambda t: t['trip_id']):
        for a, b in zip(trip['visits'], trip['visits'][1:]):
            identity = (trip['route_id'], trip['shape_id'], a['stop_id'], b['stop_id'])
            mapping.append(dict(trip_id=trip['trip_id'], from_stop_sequence=a['stop_sequence'],
                                to_stop_sequence=b['stop_sequence'], shared_arc_id=identity_to_group.get(identity)))
    if not groups:
        raise ValueError('No shared segment passed geometry checks; do not enable SHARED')
    hashes = {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest()
              for name in ('trips.json', 'stops.json', 'shapes.json')}
    result = dict(schema_version=1, status='snapshot_geometry_checked_not_operational_road_validation',
                  criteria=dict(anchor_limit_m=ANCHOR_LIMIT_M, sampled_deviation_limit_m=MATCH_LIMIT_M,
                                length_ratio_limit=LENGTH_RATIO_LIMIT, samples_per_segment=SAMPLES,
                                clustering='complete_pairwise_agreement_not_transitive_proximity'),
                  source_sha256=hashes, groups=groups, segment_mapping=mapping, rejected=rejections)
    (OUT / 'shared_geometry.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    summary = dict(status=result['status'], criteria=result['criteria'], shared_groups=len(groups),
                   shared_stop_pairs=len({(g['from_stop_id'], g['to_stop_id']) for g in groups}),
                   geometry_variants_rejected=len(rejections), operating_trip_segments=len(mapping),
                   mapped_shared_trip_segments=sum(m['shared_arc_id'] is not None for m in mapping),
                   shared_geometry_sha256=hashlib.sha256((OUT / 'shared_geometry.json').read_bytes()).hexdigest())
    (ROOT / 'reports/phase2_shared_geometry.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
