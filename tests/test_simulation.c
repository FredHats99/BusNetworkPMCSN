#include "rome_bus_pmcsn/simulation.h"
#include <math.h>
#include <stdio.h>
#include <string.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr, "Failure line %d: %s\n", __LINE__, #x); return 1; } } while (0)

int main(void) {
    PmRng rng, copy;
    double u;
    CHECK(pm_rng_init(&rng, 0) != 0);
    CHECK(pm_rng_init(&rng, 1) == 0);
    CHECK(rng.state[1] == 22925);
    for (unsigned i = 0; i < 10000; ++i) CHECK(pm_rng_uniform(&rng, 0, &u) == 0 && u > 0 && u < 1);
    CHECK(rng.state[0] == 399268537 && rng.draws[0] == 10000);
    rng.draws[0] = PMCSN_STREAM_SPACING-1;
    copy = rng;
    CHECK(pm_rng_uniform(&rng, 0, &u) != 0 && memcmp(&rng, &copy, sizeof(rng)) == 0);
    CHECK(pm_rng_uniform(&rng, 256, &u) != 0);
    CHECK(pm_rng_init_network(&rng, 12345) == 0);
    CHECK(pm_rng_uniform(&rng, 0, &u) == 0 && fabs(u-0.12701112204657714) < 1e-15);
    CHECK(pm_rng_uniform(&rng, 0, &u) == 0 && fabs(u-0.3185275653967945) < 1e-15);
    CHECK(pm_rng_uniform(&rng, 0, &u) == 0 && fabs(u-0.3091860155832701) < 1e-15);
    rng.draws[0] = UINT64_MAX; copy = rng;
    CHECK(pm_rng_uniform(&rng, 0, &u) != 0 && memcmp(&rng, &copy, sizeof(rng)) == 0);

    PmCalendar q = {0};
    PmEvent e = {0};
    e.route = e.direction = e.trip = ""; e.sequence = -1;
    /* Exercise heap expansion and both even and odd heap lengths. */
    for (int i = 999; i >= 0; --i) { e.time = i; CHECK(pm_calendar_push(&q, e) == 0); }
    for (int i = 0; i < 1000; ++i) CHECK(pm_calendar_pop(&q, &e) && e.time == i);
    e.time = 1; e.priority = 5; CHECK(pm_calendar_push(&q, e) == 0);
    e.priority = 1; CHECK(pm_calendar_push(&q, e) == 0);
    CHECK(pm_calendar_pop(&q, &e) && e.priority == 1);
    CHECK(pm_calendar_pop(&q, &e) && e.priority == 5);
    e.time = 1; e.priority = 5; e.route = "Z"; CHECK(pm_calendar_push(&q, e) == 0);
    e.route = "A"; e.direction = "1"; CHECK(pm_calendar_push(&q, e) == 0);
    e.direction = "0"; e.trip = "Z"; CHECK(pm_calendar_push(&q, e) == 0);
    e.trip = "A"; e.sequence = 2; CHECK(pm_calendar_push(&q, e) == 0);
    e.sequence = 1; e.passenger = 2; CHECK(pm_calendar_push(&q, e) == 0);
    e.passenger = 1; CHECK(pm_calendar_push(&q, e) == 0);
    CHECK(pm_calendar_push(&q, e) == 0);
    uint64_t serial;
    CHECK(pm_calendar_pop(&q, &e) && e.passenger == 1); serial = e.serial;
    CHECK(pm_calendar_pop(&q, &e) && e.passenger == 1 && e.serial > serial);
    CHECK(pm_calendar_pop(&q, &e) && e.passenger == 2);
    CHECK(pm_calendar_pop(&q, &e) && e.sequence == 2);
    CHECK(pm_calendar_pop(&q, &e) && !strcmp(e.trip, "Z"));
    CHECK(pm_calendar_pop(&q, &e) && !strcmp(e.direction, "1"));
    CHECK(pm_calendar_pop(&q, &e) && !strcmp(e.route, "Z"));
    e.time = NAN; CHECK(pm_calendar_push(&q, e) != 0);
    pm_calendar_destroy(&q);

    PmControlledConfig c = {20, 10, 0, 2};
    const double times[] = {1, 2, 3, 10, 11, 20};
    PmControlledResult r;
    CHECK(pm_controlled_run(&c, times, 6, &r, NULL) == 0);
    CHECK(r.arrivals == 5 && r.boarded == 2 && r.residual == 3 && r.buses == 1);
    CHECK(r.denied_events == 2 && r.denied_passengers == 2);
    CHECK(r.queue_area == 53 && r.wait_sum == 53 && r.mean_wait == 10.6);
    c.horizon = 30;
    CHECK(pm_controlled_run(&c, times, 6, &r, NULL) == 0);
    CHECK(r.arrivals == 6 && r.boarded == 4 && r.residual == 2 && r.buses == 2);
    CHECK(r.denied_events == 4 && r.denied_passengers == 4);
    CHECK(r.queue_area == 73 && r.wait_sum == 73);
    CHECK(pm_controlled_run(&c, NULL, 0, &r, NULL) == 0);
    CHECK(r.arrivals == 0 && r.queue_area == 0 && isnan(r.mean_wait));
    const double bad[] = {2, 1};
    CHECK(pm_controlled_run(&c, bad, 2, &r, NULL) != 0);
    c.capacity = 0; CHECK(pm_controlled_run(&c, NULL, 0, &r, NULL) != 0);
    c.capacity = 2; c.rate = .8;
    CHECK(pm_rng_init(&rng, 123456789) == 0); copy = rng;
    PmControlledResult r2;
    CHECK(pm_controlled_random(&c, &rng, &r, NULL) == 0);
    CHECK(pm_controlled_random(&c, &copy, &r2, NULL) == 0);
    CHECK(r.arrivals == r2.arrivals && r.wait_sum == r2.wait_sum);
    CHECK(memcmp(&rng, &copy, sizeof(rng)) == 0);
    CHECK(pm_controlled_random(&c, &rng, &r, NULL) == 0);
    CHECK(rng.draws[0] > copy.draws[0]);
    return 0;
}
