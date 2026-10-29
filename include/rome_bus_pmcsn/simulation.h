#ifndef PMCSN_SIMULATION_H
#define PMCSN_SIMULATION_H
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

#define PMCSN_STREAMS 256
#define PMCSN_STREAM_SPACING UINT64_C(8367782)
typedef struct {
    unsigned algorithm; /* 0: Lehmer 256-stream controlled; 1: Lehmer four-block network */
    uint32_t root_seed;
    uint32_t state[PMCSN_STREAMS];
    uint64_t draws[PMCSN_STREAMS];
    uint64_t ceiling[4]; /* Network invocation caps; default to global block limits. */
} PmRng;
int pm_rng_init(PmRng *rng, uint32_t seed);
int pm_rng_init_network(PmRng *rng, uint32_t seed);
uint64_t pm_rng_network_offset(unsigned stream);
uint64_t pm_rng_limit(const PmRng *rng, unsigned stream);
/* Advance within a block in O(log count); failed operations leave RNG intact. */
int pm_rng_advance(PmRng *rng, unsigned stream, uint64_t count);
int pm_rng_set_ceiling(PmRng *rng, const uint64_t ceiling[4]);
/* Returns -1 before a draw would reach the next stream's initial state. */
int pm_rng_uniform(PmRng *rng, unsigned stream, double *value);

/* Lower priority numbers run first. Strings are borrowed until pop/destroy.
 * Use empty strings and -1 for inapplicable fields. Payload ownership is caller's. */
typedef struct {
    double time;
    unsigned priority;
    const char *route, *direction, *trip;
    int sequence;
    uint64_t passenger, serial;
    size_t payload;
    unsigned kind;
} PmEvent;
typedef struct { PmEvent *items; size_t size, capacity; uint64_t serial; } PmCalendar;
int pm_calendar_push(PmCalendar *calendar, PmEvent event);
int pm_calendar_pop(PmCalendar *calendar, PmEvent *event);
void pm_calendar_destroy(PmCalendar *calendar);

typedef struct {
    double horizon, headway, rate;
    size_t capacity;
} PmControlledConfig;
typedef struct {
    uint64_t arrivals, boarded, residual, denied_events, denied_passengers, buses;
    double queue_area, wait_sum, mean_wait, mean_queue;
} PmControlledResult;
/* Deterministic arrivals are sorted nonnegative times; events at T are excluded.
 * trace may be NULL, otherwise CSV with counts and cumulative queue area.
 * Output is assigned only on success; all working allocations are released. */
int pm_controlled_run(const PmControlledConfig *config, const double *arrivals,
                      size_t count, PmControlledResult *result, FILE *trace);
/* Consumes stream 0, continues caller-owned RNG across runs. */
int pm_controlled_random(const PmControlledConfig *config, PmRng *rng,
                         PmControlledResult *result, FILE *trace);
int pm_simulation_cli(int argc, char **argv);
int pm_network_run(const char *path, PmRng *rng, uint64_t replica, FILE *out, FILE *trace);
/* Travel diagnostics never draw RNG values or change the event calendar. */
int pm_network_run_diagnostic(const char *path, PmRng *rng, uint64_t replica,
                              FILE *out, FILE *trace, FILE *travel);
#endif
