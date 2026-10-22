"""Build explicit synthetic initial states; no random draws or simulated history."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/processed/phase2'


def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


def balanced_destination(support, index, count):
    return support[min(len(support)-1, int((index+0.5)*len(support)/count))]


def main():
    assumptions_path = ROOT / 'configs/phase2_assumptions.json'
    assumptions = json.loads(assumptions_path.read_text(encoding='utf-8'))
    init = assumptions['initialization']
    scenario = read('synthetic_scenarios.json')
    start = assumptions['terminal']['window_seconds'][0]
    assignments = {a['trip_id']: a for a in scenario['fleet_assignments']}
    directions = {(r['route_id'], r['direction_id']): r for r in scenario['normalization_references']}
    multipliers = {'BASE': 1.0, 'REGULAR': 1.0, 'SHARED': 1.0,
                   'D075': 0.75, 'D125': 1.25, 'SHARED_D125': 1.25}
    buses = []
    for trip in sorted(read('trips.json'), key=lambda t: t['trip_id']):
        if trip['window_role'] != 'already_in_progress':
            continue
        upcoming = next(i for i, v in enumerate(trip['visits']) if v['arrival_seconds'] >= start)
        before, after = trip['visits'][upcoming-1], trip['visits'][upcoming]
        fraction = (start-before['departure_seconds'])/(after['arrival_seconds']-before['departure_seconds'])
        capacity = assignments[trip['trip_id']]['capacity_passengers']
        count = math.floor(capacity*init['loaded_onboard_fraction'])
        support = [dict(stop_id=v['stop_id'], stop_sequence=v['stop_sequence'])
                   for v in trip['visits'][upcoming:] if v['dropoff_allowed']]
        if not 0 <= fraction <= 1 or not support:
            raise ValueError('Invalid scheduled initial position or destination support')
        buses.append(dict(trip_id=trip['trip_id'], capacity_passengers=capacity,
                          previous_stop_sequence=before['stop_sequence'], next_stop_sequence=after['stop_sequence'],
                          scheduled_segment_fraction=fraction, next_arrival_seconds=after['arrival_seconds'],
                          empty_passengers_onboard=[],
                          loaded_passengers_onboard=[dict(passenger_id=f'initial-bus-{trip["trip_id"]}-{i:04}',
                                                          destination=balanced_destination(support, i, count),
                                                          initial_cohort=True, original_boarding_time=None)
                                                     for i in range(count)]))
    loaded_queues = {}
    for sid, multiplier in multipliers.items():
        queues = []
        for queue in scenario['queue_demand']:
            reference = directions[(queue['route_id'], queue['direction_id'])]
            max_age = reference['nominal_headway_seconds']/2
            count = math.floor(queue['baseline_rates_passengers_per_second'][0]*multiplier*max_age)
            support = queue['admissible_destination_stop_ids']
            qid = f'{queue["route_id"]}-{queue["direction_id"]}-{queue["stop_id"]}'
            # Oldest first, preserving FIFO. Initial destination assignments are balanced, not iid draws.
            passengers = [dict(passenger_id=f'initial-queue-{sid}-{qid}-{i:04}',
                               arrival_seconds=start-max_age*(count-i-0.5)/count,
                               destination_stop_id=balanced_destination(support, i, count),
                               initial_cohort=True) for i in range(count)]
            queues.append(dict(route_id=queue['route_id'], direction_id=queue['direction_id'],
                               stop_id=queue['stop_id'], passengers=passengers))
        loaded_queues[sid] = queues
    hashes = {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest()
              for name in ('trips.json', 'synthetic_scenarios.json')}
    result = dict(schema_version=1, status='explicit_synthetic_states_not_observed_or_equilibrated',
                  assumptions_sha256=hashlib.sha256(assumptions_path.read_bytes()).hexdigest(),
                  source_sha256=hashes, start_seconds=start, initial_buses=buses,
                  empty_passengers_initial_queues=[], loaded_initial_queues_by_scenario=loaded_queues)
    path = OUT / 'initial_states.json'
    path.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    summary = dict(initial_buses=len(buses), empty_initial_passengers=0,
                   loaded_onboard_passengers=sum(len(b['loaded_passengers_onboard']) for b in buses),
                   loaded_queued_passengers_by_scenario={sid: sum(len(q['passengers']) for q in queues)
                                                        for sid, queues in loaded_queues.items()},
                   initial_states_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    (ROOT / 'reports/phase2_initial_states.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
