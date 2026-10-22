"""Audit generated phase-2 inputs and their provenance without simulation."""
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/processed/phase2'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    manifest = read(OUT / 'manifest.json')
    for name, expected in manifest['source_sha256'].items():
        with (ROOT / manifest['source'] / name).open('rb') as handle:
            require(hashlib.file_digest(handle, 'sha256').hexdigest() == expected, f'Source hash: {name}')
    for name, expected in manifest['output_sha256'].items():
        with (OUT / name).open('rb') as handle:
            require(hashlib.file_digest(handle, 'sha256').hexdigest() == expected, f'Output hash: {name}')
    trips = read(OUT / 'trips.json')
    original_audit = read(ROOT / 'reports/network_sample_audit.json')
    require(len(trips) == original_audit['checked_active_day_trips'], 'Active day trip count')
    require(sum(t['window_role'] == 'window_departure' for t in trips) == original_audit['window_departures'],
            'Window departure count')
    require(sum(t['window_role'] == 'already_in_progress' for t in trips)
            == sum(original_audit['trips_in_progress_at_0700'].values()), 'Initial vehicle count')
    scenario = read(OUT / 'synthetic_scenarios.json')
    assumptions_path = ROOT / 'configs/phase2_assumptions.json'
    require(scenario['assumptions_sha256'] == hashlib.sha256(assumptions_path.read_bytes()).hexdigest(),
            'Synthetic assumptions changed')
    trip_ids = {t['trip_id'] for t in trips}
    assignments = scenario['fleet_assignments']
    require(len(assignments) == len(trip_ids) and {a['trip_id'] for a in assignments} == trip_ids,
            'Every trip must have exactly one vehicle assignment')
    classes = Counter(a['vehicle_class'] for a in assignments)
    for reference in scenario['normalization_references']:
        load = (reference['baseline_rate_passengers_per_second'] * reference['nominal_headway_seconds']
                * reference['max_unit_rate_pattern_load_coefficient'])
        require(math.isclose(load/reference['mean_assigned_window_capacity'], reference['target_fraction']),
                'Nominal target normalization')
    raw_queues = read(OUT / 'queues.json')
    require(len(scenario['queue_demand']) == len(raw_queues), 'Demand must cover all exported queues')
    keys = [(q['route_id'], q['direction_id'], q['stop_id']) for q in scenario['queue_demand']]
    require(len(keys) == len(set(keys)), 'Duplicate demand queue')
    for queue in scenario['queue_demand']:
        require(queue['admissible_destination_stop_ids'], 'Empty OD support')
        require(len(queue['baseline_rates_passengers_per_second']) == 8
                and all(math.isfinite(v) and v > 0 for v in queue['baseline_rates_passengers_per_second']),
                'Invalid demand bins')
    travel_path = ROOT / scenario['travel_reference_file']
    require(hashlib.sha256(travel_path.read_bytes()).hexdigest() == scenario['travel_reference_sha256'],
            'Travel reference hash')
    travel = read(travel_path)
    segments = travel['segments']
    model = travel['stochastic_model']
    log_location, log_scale = model['normal_log_location'], model['normal_log_scale']
    require(math.isclose(math.exp(log_location+log_scale*log_scale/2), 1.0), 'Lognormal multiplier mean')
    require(math.isclose(math.sqrt(math.expm1(log_scale*log_scale)), model['multiplier_cv']),
            'Lognormal multiplier CV')
    require(model['regular_multiplier'] == 1.0, 'Regular scenario multiplier')
    expected_gaps = {(t['trip_id'], a['stop_sequence'], b['stop_sequence']):
                     b['arrival_seconds']-a['departure_seconds']
                     for t in trips if t['window_role'] != 'outside_window'
                     for a, b in zip(t['visits'], t['visits'][1:])}
    require(len(segments) == len(expected_gaps), 'Derived travel segment coverage')
    segment_keys = {(s['trip_id'], s['from_stop_sequence'], s['to_stop_sequence']) for s in segments}
    require(segment_keys == set(expected_gaps), 'Derived travel segment keys')
    for segment in segments:
        key = (segment['trip_id'], segment['from_stop_sequence'], segment['to_stop_sequence'])
        require(segment['reference_travel_seconds'] > 0, 'Nonpositive reference travel')
        require(math.isclose(segment['reference_travel_seconds']+segment['reference_dwell_seconds'],
                             expected_gaps[key]), 'Travel/dwell reference must reconstruct GTFS gap')
    geometry_path = OUT / 'shared_geometry.json'
    require(hashlib.sha256(geometry_path.read_bytes()).hexdigest() == scenario['shared_geometry_sha256'],
            'Shared geometry hash')
    geometry = read(geometry_path)
    for name, expected in geometry['source_sha256'].items():
        require(hashlib.sha256((OUT / name).read_bytes()).hexdigest() == expected, f'Geometry source: {name}')
    groups = {g['shared_arc_id']: g for g in geometry['groups']}
    require(groups, 'Empty shared geometry domain')
    criteria = geometry['criteria']
    for group in groups.values():
        require(len(set(group['route_ids'])) >= 2, 'Shared group must include different routes')
        require(group['max_sampled_deviation_m'] <= criteria['sampled_deviation_limit_m']
                and group['maximum_anchor_error_m'] <= criteria['anchor_limit_m']
                and group['max_length_ratio'] <= criteria['length_ratio_limit'], 'Shared geometry thresholds')
    mapping = {(s['trip_id'], s['from_stop_sequence'], s['to_stop_sequence']): s['shared_arc_id']
               for s in geometry['segment_mapping']}
    require(len(mapping) == len(geometry['segment_mapping']) and set(mapping) == set(expected_gaps),
            'Shared domain mapping coverage')
    trip_lookup = {t['trip_id']: t for t in trips}
    for segment in segments:
        key = (segment['trip_id'], segment['from_stop_sequence'], segment['to_stop_sequence'])
        gid = mapping[key]
        require(segment['shared_arc_id'] == gid, 'Travel/geometry mapping consistency')
        if gid is not None:
            trip = trip_lookup[segment['trip_id']]
            require([trip['route_id'], trip['shape_id'], segment['from_stop_id'], segment['to_stop_id']]
                    in groups[gid]['members'], 'Shared group membership')
    initial_path = OUT / 'initial_states.json'
    initial = read(initial_path)
    require(initial['assumptions_sha256'] == scenario['assumptions_sha256'], 'Initial state assumptions hash')
    for name, expected in initial['source_sha256'].items():
        require(hashlib.sha256((OUT / name).read_bytes()).hexdigest() == expected, f'Initial state source: {name}')
    initial_buses = initial['initial_buses']
    expected_initial = {t['trip_id'] for t in trips if t['window_role'] == 'already_in_progress'}
    require(len(initial_buses) == len(expected_initial)
            and {b['trip_id'] for b in initial_buses} == expected_initial, 'Initial vehicle coverage')
    initial_ids = set()
    for bus in initial_buses:
        trip = trip_lookup[bus['trip_id']]
        remaining = {(v['stop_id'], v['stop_sequence']) for v in trip['visits']
                     if v['stop_sequence'] >= bus['next_stop_sequence'] and v['dropoff_allowed']}
        require(0 <= bus['scheduled_segment_fraction'] <= 1, 'Initial route position')
        require(bus['next_arrival_seconds'] >= initial['start_seconds'], 'Initial event before start')
        require(not bus['empty_passengers_onboard'], 'Empty-state onboard load')
        require(len(bus['loaded_passengers_onboard']) <= bus['capacity_passengers'], 'Initial capacity')
        for passenger in bus['loaded_passengers_onboard']:
            require((passenger['destination']['stop_id'], passenger['destination']['stop_sequence']) in remaining,
                    'Initial onboard destination unreachable')
            require(passenger['passenger_id'] not in initial_ids, 'Duplicate initial onboard passenger')
            initial_ids.add(passenger['passenger_id'])
    support = {(q['route_id'], q['direction_id'], q['stop_id']): set(q['admissible_destination_stop_ids'])
               for q in scenario['queue_demand']}
    require(set(initial['loaded_initial_queues_by_scenario']) == set(scenario['scenario_multipliers']),
            'Initial states must cover every scenario')
    for sid, initial_queues in initial['loaded_initial_queues_by_scenario'].items():
        require(len(initial_queues) == len(support), 'Initial queue coverage')
        for queue in initial_queues:
            key = (queue['route_id'], queue['direction_id'], queue['stop_id'])
            timestamps = [p['arrival_seconds'] for p in queue['passengers']]
            require(timestamps == sorted(timestamps) and all(t < initial['start_seconds'] for t in timestamps),
                    'Initial queue FIFO and pre-window arrival times')
            require(all(p['destination_stop_id'] in support[key] and p['initial_cohort']
                        for p in queue['passengers']), 'Initial queue destinations/cohort')
    assumptions = read(assumptions_path)
    require('pending' not in json.dumps(assumptions), 'Unresolved operational assumption')
    require(assumptions['terminal']['end_exclusive'] and assumptions['terminal']['window_seconds'] == [25200, 39600],
            'Finite-horizon boundary')
    require(scenario['operational_rules'] == {name: assumptions[name]
            for name in ('dwell', 'termini', 'initialization', 'terminal', 'events')}, 'Compiled operational rules')
    report = dict(status='passed_input_consistency_not_simulator_validation', active_day_trips=len(trips),
                  derived_travel_segments=len(segments),
                  minimum_reference_travel_seconds=min(s['reference_travel_seconds'] for s in segments),
                  shared_geometry_groups=len(groups), initial_buses=len(initial_buses),
                  queues=len(keys), fleet_classes=dict(classes),
                  checks=['source_and_output_hashes', 'independent_prior_audit_counts',
                          'complete_unique_fleet_assignment', 'nominal_demand_normalization',
                          'positive_finite_rates_eight_bins', 'travel_reference_coverage_and_gtfs_reconstruction',
                          'lognormal_analytical_mean_cv_and_regular_multiplier',
                          'shared_geometry_provenance_thresholds_and_membership',
                          'initial_state_destinations_capacity_fifo_and_cohort',
                          'operational_rules_complete_and_finite_horizon'],
                  synthetic_scenarios_sha256=hashlib.sha256((OUT / 'synthetic_scenarios.json').read_bytes()).hexdigest())
    (ROOT / 'reports/phase2_input_checks.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    config_files = ['configs/phase2_assumptions.json', 'configs/network.yaml',
                    'configs/simulation.yaml', 'configs/experiments.yaml']
    generated = ['manifest.json', 'trips.json', 'patterns.json', 'stops.json', 'arcs.json',
                 'queues.json', 'shapes.json', 'shared_geometry.json', 'travel_reference.json',
                 'synthetic_scenarios.json', 'initial_states.json']
    freeze = dict(status='phase2_inputs_frozen_not_simulation_results', date=assumptions['freeze_date'],
                  source_gtfs_sha256=manifest['source_sha256'],
                  configurations_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in config_files},
                  generated_sha256={p: hashlib.sha256((OUT/p).read_bytes()).hexdigest() for p in generated},
                  specification_and_tools_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in
                      ['docs/phase2_operational_contract.md', 'scripts/prepare_phase2.py',
                       'scripts/prepare_shared_geometry.py', 'scripts/prepare_phase2_scenarios.py',
                       'scripts/prepare_initial_states.py', 'scripts/audit_phase2_inputs.py',
                       'tests/test_phase2_geometry.py']},
                  phase3_gates=['c_simulator_implementation_and_verification', 'rng_adequacy',
                                'actual_factor_marginals', 'plausibility_and_runtime'],
                  phase4_gate='transient_horizon_and_initial_state_assessment')
    (ROOT / 'reports/phase2_freeze.json').write_text(json.dumps(freeze, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
