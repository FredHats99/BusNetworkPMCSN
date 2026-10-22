#include "rome_bus_pmcsn/simulation.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

enum { ARRIVAL, BUS };
typedef struct { double arrival; int denied; } Passenger;
typedef struct {
    Passenger *people;
    size_t size, allocated, head;
    PmCalendar calendar;
    PmControlledResult result;
} Run;

static int valid(const PmControlledConfig *c) {
    return c && isfinite(c->horizon) && c->horizon > 0 &&
        isfinite(c->headway) && c->headway > 0 && c->capacity > 0 &&
        isfinite(c->rate) && c->rate >= 0;
}

static int schedule(Run *r, double time, unsigned kind, uint64_t id) {
    PmEvent e = {0};
    e.time = time; e.priority = kind == ARRIVAL ? 1 : 4;
    e.route = e.direction = e.trip = ""; e.sequence = -1;
    e.kind = kind; e.passenger = id;
    return pm_calendar_push(&r->calendar, e);
}

static int append(Run *r, double t) {
    if (r->size == r->allocated) {
        size_t n = r->allocated ? r->allocated * 2 : 256;
        if (n < r->allocated || n > SIZE_MAX / sizeof(Passenger)) return -1;
        Passenger *p = realloc(r->people, n * sizeof(*p));
        if (!p) return -1;
        r->people = p; r->allocated = n;
    }
    r->people[r->size++] = (Passenger){t, 0};
    ++r->result.arrivals; return 0;
}

static int next_arrival(Run *r, const PmControlledConfig *c, PmRng *rng, double t) {
    if (c->rate == 0) return 0;
    double u;
    if (pm_rng_uniform(rng, 0, &u)) return -1;
    double next = t - log(u) / c->rate;
    /* Reject rates below the representable time resolution rather than loop. */
    if (next <= t) return -1;
    return next < c->horizon ? schedule(r, next, ARRIVAL, r->result.arrivals) : 0;
}

static int execute(const PmControlledConfig *c, const double *times, size_t count,
                   PmRng *rng, PmControlledResult *out, FILE *trace) {
    if (!valid(c) || !out || (!rng && count && !times)) return -1;
    Run r; memset(&r, 0, sizeof(r));
    int rc = -1;
    double last = 0;
    if (rng) {
        if (next_arrival(&r, c, rng, 0)) goto done;
    } else {
        for (size_t i = 0; i < count; ++i) {
            if (!isfinite(times[i]) || times[i] < 0 || (i && times[i] < times[i-1])) goto done;
            if (times[i] < c->horizon && schedule(&r, times[i], ARRIVAL, i)) goto done;
        }
    }
    /* Empty immediately after t=0; first service at h, not at 0. */
    if (c->headway < c->horizon && schedule(&r, c->headway, BUS, 0)) goto done;
    if (trace && fprintf(trace, "time,event,arrivals,boarded,queue,queue_area\n") < 0) goto done;
    PmEvent e;
    while (pm_calendar_pop(&r.calendar, &e)) {
        r.result.queue_area += (e.time - last) * (double)(r.size - r.head);
        last = e.time;
        if (e.kind == ARRIVAL) {
            if (append(&r, e.time)) goto done;
            if (rng && next_arrival(&r, c, rng, e.time)) goto done;
        } else {
            size_t waiting = r.size - r.head;
            size_t boarded = waiting < c->capacity ? waiting : c->capacity;
            for (size_t j = 0; j < boarded; ++j)
                r.result.wait_sum += e.time - r.people[r.head++].arrival;
            r.result.boarded += boarded;
            ++r.result.buses;
            for (size_t j = r.head; j < r.size; ++j) {
                ++r.result.denied_events;
                if (!r.people[j].denied) { r.people[j].denied = 1; ++r.result.denied_passengers; }
            }
            double next = (double)(r.result.buses + 1) * c->headway;
            if (next <= e.time) goto done;
            if (next < c->horizon && schedule(&r, next, BUS, 0)) goto done;
        }
        if (trace && fprintf(trace, "%.17g,%s,%llu,%llu,%zu,%.17g\n", e.time,
                e.kind == ARRIVAL ? "arrival" : "bus",
                (unsigned long long)r.result.arrivals, (unsigned long long)r.result.boarded,
                r.size-r.head, r.result.queue_area) < 0) goto done;
    }
    r.result.queue_area += (c->horizon-last) * (double)(r.size-r.head);
    for (size_t j = r.head; j < r.size; ++j) r.result.wait_sum += c->horizon-r.people[j].arrival;
    r.result.residual = r.size-r.head;
    r.result.mean_queue = r.result.queue_area/c->horizon;
    r.result.mean_wait = r.result.arrivals ? r.result.wait_sum/(double)r.result.arrivals : NAN;
    if (r.result.arrivals != r.result.boarded+r.result.residual ||
        fabs(r.result.wait_sum-r.result.queue_area) > 1e-8 * fmax(1, r.result.queue_area)) goto done;
    if (trace && fprintf(trace, "%.17g,horizon,%llu,%llu,%llu,%.17g\n", c->horizon,
            (unsigned long long)r.result.arrivals, (unsigned long long)r.result.boarded,
            (unsigned long long)r.result.residual, r.result.queue_area) < 0) goto done;
    *out = r.result; rc = 0;
done:
    free(r.people); pm_calendar_destroy(&r.calendar); return rc;
}

int pm_controlled_run(const PmControlledConfig *c, const double *arrivals, size_t count,
                      PmControlledResult *out, FILE *trace) {
    return execute(c, arrivals, count, NULL, out, trace);
}

int pm_controlled_random(const PmControlledConfig *c, PmRng *rng,
                         PmControlledResult *out, FILE *trace) {
    if (!rng) return -1;
    return execute(c, NULL, 0, rng, out, trace);
}
