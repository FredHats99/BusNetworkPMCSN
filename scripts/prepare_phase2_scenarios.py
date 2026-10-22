"""Compile explicit synthetic inputs from the offline phase-2 extraction."""
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/processed/phase2'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    config_path = ROOT / 'configs/phase2_assumptions.json'
    assumptions = read(config_path)
    trips = read(OUT / 'trips.json')
    queues = read(OUT / 'queues.json')
    geometry_path = OUT / 'shared_geometry.json'
    geometry = read(geometry_path)
    shared_mapping = {(s['trip_id'], s['from_stop_sequence'], s['to_stop_sequence']): s['shared_arc_id']
                      for s in geometry['segment_mapping']}
    patterns = {p['pattern_id']: p for p in read(OUT / 'patterns.json')}
    by_direction = defaultdict(list)
    for trip in trips:
        by_direction[(trip['route_id'], trip['direction_id'])].append(trip)
    assignments, rates, references = [], [], []
    for key, group in sorted(by_direction.items()):
        group.sort(key=lambda t: (t['start_seconds'], t['trip_id']))
        window = [t for t in group if t['window_role'] == 'window_departure']
        if not window:
            raise ValueError(f'No scheduled departures: {key}')
        for index, trip in enumerate(group):
            vehicle_class = 'standard_12m' if index % 2 == 0 else 'articulated_18m'
            capacity = assumptions['capacity_passengers'][vehicle_class]
            assignments.append(dict(trip_id=trip['trip_id'], route_id=key[0], direction_id=key[1],
                                    vehicle_class=vehicle_class, capacity_passengers=capacity,
                                    window_role=trip['window_role']))
        local_assignments = {a['trip_id']: a for a in assignments if (a['route_id'], a['direction_id']) == key}
        mean_capacity = sum(local_assignments[t['trip_id']]['capacity_passengers'] for t in window)/len(window)
        # Nominal whole-window headway, not an observed mean or a per-bin guarantee.
        headway = 14400 / len(window)
        peaks = []
        for pid in sorted({t['pattern_id'] for t in group if t['window_role'] != 'outside_window'}):
            visits = patterns[pid]['visits']
            if patterns[pid]['repeated_stop_ids'] or not all(pickup and dropoff for _, pickup, dropoff in visits):
                raise ValueError('The normalization adapter requires a simple unrestricted pattern')
            m = len(visits)
            peak = max(sum((m-i)/(m-a) for a in range(1, i+1)) for i in range(1, m))
            peaks.append(peak)
        target = assumptions['demand']['nominal_peak_segment_load_fraction']
        rate = target*mean_capacity/(headway*max(peaks))
        references.append(dict(route_id=key[0], direction_id=key[1],
                               nominal_headway_seconds=headway, mean_assigned_window_capacity=mean_capacity,
                               max_unit_rate_pattern_load_coefficient=max(peaks),
                               baseline_rate_passengers_per_second=rate,
                               target_fraction=target, interpretation='nominal_reference_not_empirical_or_stability_claim'))
        for queue in queues:
            if (queue['route_id'], queue['direction_id']) != key:
                continue
            rates.append(dict(route_id=key[0], direction_id=key[1], stop_id=queue['stop_id'],
                              baseline_rates_passengers_per_second=[rate*f for f in assumptions['demand']['bin_multipliers']],
                              admissible_destination_stop_ids=queue['destinations']))
    reference_dwell = assumptions['travel']['reference_dwell_seconds']
    if not math.isfinite(reference_dwell) or reference_dwell < 0:
        raise ValueError('Reference dwell must be finite and nonnegative')
    travel_segments = []
    for trip in trips:
        if trip['window_role'] == 'outside_window':
            continue
        for current, following in zip(trip['visits'], trip['visits'][1:]):
            gap = following['arrival_seconds'] - current['departure_seconds']
            travel = gap - reference_dwell
            if travel <= 0:
                raise ValueError(f'Nonpositive derived travel time: {trip["trip_id"]}')
            travel_segments.append(dict(trip_id=trip['trip_id'], from_stop_sequence=current['stop_sequence'],
                                        to_stop_sequence=following['stop_sequence'],
                                        from_stop_id=current['stop_id'], to_stop_id=following['stop_id'],
                                        programmed_gap_seconds=gap, reference_dwell_seconds=reference_dwell,
                                        reference_travel_seconds=travel,
                                        shared_arc_id=shared_mapping[(trip['trip_id'], current['stop_sequence'], following['stop_sequence'])]))
    travel_path = OUT / 'travel_reference.json'
    cv = assumptions['travel']['positive_cv']
    if not math.isfinite(cv) or cv < 0:
        raise ValueError('Travel CV must be finite and nonnegative')
    log_variance = math.log1p(cv*cv)
    travel_model = dict(distribution='lognormal_multiplier', multiplier_mean=1.0, multiplier_cv=cv,
                        normal_log_location=-log_variance/2, normal_log_scale=math.sqrt(log_variance),
                        regular_multiplier=1.0,
                        environment_bin_seconds=assumptions['travel']['environment_bin_seconds'],
                        factor_selection_time=assumptions['travel']['factor_selection_time'],
                        independent_factor_key=assumptions['travel']['independent_factor_key'],
                        factor_reuse=assumptions['travel']['factor_reuse'],
                        shared_status=assumptions['travel']['shared_factor_status'],
                        shared_domain_file=assumptions['travel']['shared_geometry_domain'],
                        independent_key_inside_domain=assumptions['travel']['independent_key_inside_domain'],
                        shared_key_inside_domain=assumptions['travel']['shared_key_inside_domain'],
                        outside_shared_domain=assumptions['travel']['outside_shared_domain'],
                        realized_traversal_marginals_status='must_check_endogenous_time_selection')
    travel_path.write_text(json.dumps(dict(status='synthetic_decomposition_not_observed_motion',
                                          stochastic_model=travel_model,
                                          segments=travel_segments), indent=2)+'\n', encoding='utf-8')
    result = dict(schema_version=1, status=assumptions['status'],
                  assumptions_sha256=hashlib.sha256(config_path.read_bytes()).hexdigest(),
                  fleet_assignments=assignments, queue_demand=rates, normalization_references=references,
                  travel_reference_file='data/processed/phase2/travel_reference.json',
                  travel_reference_sha256=hashlib.sha256(travel_path.read_bytes()).hexdigest(),
                  shared_geometry_sha256=hashlib.sha256(geometry_path.read_bytes()).hexdigest(),
                  operational_rules={name: assumptions[name] for name in ('dwell', 'termini', 'initialization', 'terminal', 'events')},
                  scenario_multipliers={'D075': 0.75, 'BASE': 1.0, 'D125': 1.25,
                                        'REGULAR': 1.0, 'SHARED': 1.0, 'SHARED_D125': 1.25},
                  nominal_load_fractions={'D075': 0.6375, 'BASE': 0.85, 'D125': 1.0625},
                  caveats=['single_pattern_reference_approximates_variant_mixture',
                           'nominal_high_load_not_a_proof_of_queue_divergence',
                           'trajectory_marginal_rng_and_runtime_gates_belong_to_phase3'])
    (OUT / 'synthetic_scenarios.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(assignments=len(assignments), queues=len(rates), directions=len(references),
                          minimum_rate_per_minute=min(r['baseline_rate_passengers_per_second']*60 for r in references),
                          maximum_rate_per_minute=max(r['baseline_rate_passengers_per_second']*60 for r in references)), indent=2))


if __name__ == '__main__':
    main()
