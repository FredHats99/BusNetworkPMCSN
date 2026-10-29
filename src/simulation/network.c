#include "rome_bus_pmcsn/simulation.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

/* Bounded input dimensions are rejected explicitly; no record is truncated. */
#define MAX_OBJECTS 4096
#define MAX_VISITS 256
#define NONE SIZE_MAX
enum { N_ARRIVE, N_BUS, N_ORIGIN, N_OPEN, N_ALIGHT, N_BOARD, N_CLOSE, N_DECIDE, N_LEG, N_SAMPLE, N_FIXED };
enum { WAITING, RESERVED, ONBOARD, FINISHED };
typedef struct {
    char route[96], direction[96]; int stop;
    int destinations[MAX_VISITS]; size_t nd;
    double rates[8]; size_t head, tail;
    uint64_t arrivals, initial, boarded, initial_boarded, denied, denied_people, local_id;
    uint64_t waiting[2]; double area[2], last, wait_sum;
    double last_bus, hw_sum, hw_square; uint64_t hw_n;
} Queue;
typedef struct { int stop, sequence, pickup, dropoff; double travel; char shared[96]; int queue; } Visit;
typedef struct {
    char route[96], direction[96], trip[96];
    Visit *visits; size_t nv, current, capacity, occupancy, head, tail, serving;
    double first_time; int origin, active, phase;
    double occupancy_area, occupancy_last;
} Bus;
typedef struct {
    size_t next, queue, destination_visit;
    int destination, state, cohort, denied;
    uint64_t id; double arrival, boarded;
} Person;
typedef struct { char key[384]; int bin; double value; } Factor;
typedef struct {
    Queue *queues; Bus *buses; size_t nq, nb;
    Person *people; size_t np, cp;
    Factor *factors; size_t nf, cf;
    size_t *factor_slots, factor_slots_capacity;
    double start, end, cv; int shared, error;
    PmCalendar calendar; PmRng *rng; FILE *trace, *travel;
    uint64_t completed, initial_onboard, initial_completed;
    double ride_sum; uint64_t ride_n;
    uint64_t replica;
} Network;

static void *grow(void *ptr, size_t *cap, size_t item) {
    size_t n = *cap ? *cap * 2 : 256;
    if (n < *cap || n > SIZE_MAX/item) return NULL;
    void *p = realloc(ptr, n*item); if (!p) return NULL;
    *cap = n; return p;
}
static double uniform(Network *n, unsigned stream) {
    double u = .5;
    if (pm_rng_uniform(n->rng, stream, &u)) n->error = 1;
    return u;
}
static void record(Network *n, double t, const char *type, size_t bus, size_t queue, size_t person, double value) {
    if (n->trace && fprintf(n->trace, "%.17g,%s,%llu,%llu,%llu,%.17g\n", t, type,
            (unsigned long long)bus, (unsigned long long)queue, (unsigned long long)person, value) < 0) n->error = 1;
}
static void event(Network *n, double t, unsigned kind, size_t index, uint64_t person) {
    if (!isfinite(t)) { n->error = 1; return; }
    if (t >= n->end) return;
    PmEvent e = {0}; e.time = t; e.kind = kind; e.payload = index; e.passenger = person; e.sequence = -1;
    e.route = e.direction = e.trip = "";
    if (kind == N_ARRIVE || kind == N_FIXED) {
        Queue *q = &n->queues[kind == N_FIXED ? n->people[index].queue : index];
        e.route = q->route; e.direction = q->direction; e.priority = 1;
    } else if (kind == N_SAMPLE) e.priority = 6;
    else {
        Bus *b = &n->buses[index]; e.route = b->route; e.direction = b->direction; e.trip = b->trip;
        e.sequence = b->visits[b->current].sequence;
        e.priority = kind == N_BUS ? 3 : kind == N_ORIGIN ? 4 : (kind == N_DECIDE || kind == N_LEG) ? 5 : 2;
    }
    if (pm_calendar_push(&n->calendar, e)) n->error = 1;
}
static void integrate(Network *n, Queue *q, double t) {
    if (t < q->last) { n->error = 1; return; }
    for (unsigned c = 0; c < 2; ++c) q->area[c] += (t-q->last)*(double)q->waiting[c];
    q->last = t;
}
static size_t person_new(Network *n, Person p) {
    if (n->np == n->cp) {
        Person *people = grow(n->people, &n->cp, sizeof(Person));
        if (!people) { n->error = 1; return NONE; }
        n->people = people;
    }
    n->people[n->np] = p; return n->np++;
}
static void enqueue(Network *n, size_t qi, size_t pi, double t) {
    Queue *q = &n->queues[qi]; integrate(n, q, t);
    n->people[pi].next = NONE;
    if (q->tail != NONE) n->people[q->tail].next = pi; else q->head = pi;
    q->tail = pi; ++q->waiting[n->people[pi].cohort];
}
static void next_arrival(Network *n, size_t qi, double t) {
    Queue *q = &n->queues[qi];
    int bin = (int)((t-n->start)/1800);
    if (bin >= 8) return;
    int positive = 0;
    for (int i = bin; i < 8; ++i) if (q->rates[i] > 0) positive = 1;
    if (!positive) return;
    double hazard = -log(uniform(n, 0));
    for (; bin < 8 && t < n->end; ++bin) {
        double limit = fmin(n->end, n->start+(bin+1)*1800.0);
        double available = (limit-t)*q->rates[bin];
        if (hazard < available) {
            double arrival = t + hazard/q->rates[bin];
            if (arrival <= t) { n->error = 1; return; }
            event(n, arrival, N_ARRIVE, qi, ((uint64_t)qi << 32) | ++q->local_id); return;
        }
        hazard -= available; t = limit;
    }
}
static size_t destination(const Bus *b, int stop) {
    for (size_t i = b->current+1; i < b->nv; ++i)
        if (b->visits[i].stop == stop && b->visits[i].dropoff) return i;
    return NONE;
}
static size_t eligible(Network *n, Bus *b) {
    Visit *v = &b->visits[b->current];
    if (!v->pickup || v->queue < 0 || b->current+1 == b->nv) return NONE;
    for (size_t p = n->queues[v->queue].head; p != NONE; p = n->people[p].next)
        if (n->people[p].state == WAITING && destination(b, n->people[p].destination) != NONE) return p;
    return NONE;
}
static void board(Network *n, Bus *b, size_t pi, double t) {
    Person *p = &n->people[pi]; Queue *q = &n->queues[p->queue]; integrate(n, q, t);
    size_t previous = NONE, current = q->head;
    while (current != NONE && current != pi) { previous = current; current = n->people[current].next; }
    if (current == NONE || !q->waiting[p->cohort] || b->occupancy >= b->capacity) { n->error = 1; return; }
    if (previous == NONE) q->head = p->next; else n->people[previous].next = p->next;
    if (q->tail == pi) q->tail = previous;
    --q->waiting[p->cohort];
    if (p->cohort) ++q->initial_boarded; else { ++q->boarded; q->wait_sum += t-p->arrival; }
    p->state = ONBOARD; p->boarded = t; p->next = NONE;
    p->destination_visit = destination(b, p->destination);
    if (p->destination_visit == NONE) { n->error = 1; return; }
    if (b->tail != NONE) n->people[b->tail].next = pi; else b->head = pi;
    b->tail = pi;
    b->occupancy_area += (t-b->occupancy_last)*(double)b->occupancy; b->occupancy_last = t;
    ++b->occupancy;
    record(n, t, "board_wait", (size_t)(b-n->buses), p->queue, pi, t-p->arrival);
}
static size_t alighter(Network *n, Bus *b) {
    for (size_t p = b->head; p != NONE; p = n->people[p].next)
        if (n->people[p].destination_visit == b->current) return p;
    return NONE;
}
static void deny(Network *n, Bus *b) {
    Visit *v = &b->visits[b->current]; if (!v->pickup || v->queue < 0) return;
    Queue *q = &n->queues[v->queue];
    for (size_t p = q->head; p != NONE; p = n->people[p].next) {
        Person *person = &n->people[p];
        if (person->state == WAITING && destination(b, person->destination) != NONE) {
            if (!person->cohort) { ++q->denied; if (!person->denied) ++q->denied_people; }
            person->denied = 1;
        }
    }
}
/* Lookup acceleration only: factor creation order, indices and RNG draws remain
 * identical to the former linear search. Zero means empty, otherwise index+1. */
static uint64_t factor_hash(const char *key, int bin) {
    uint64_t hash = UINT64_C(14695981039346656037);
    for (const unsigned char *p = (const unsigned char *)key; *p; ++p)
        hash = (hash ^ *p)*UINT64_C(1099511628211);
    return (hash ^ (uint32_t)bin)*UINT64_C(1099511628211);
}
static int factor_table_reserve(Network *n) {
    if (n->factor_slots_capacity && n->nf < n->factor_slots_capacity/2) return 0;
    size_t capacity = n->factor_slots_capacity ? n->factor_slots_capacity*2 : 1024;
    if (capacity < n->factor_slots_capacity || capacity > SIZE_MAX/sizeof(size_t)) return -1;
    size_t *slots = calloc(capacity, sizeof(*slots));
    if (!slots) return -1;
    for (size_t i = 0; i < n->nf; ++i) {
        size_t pos = (size_t)factor_hash(n->factors[i].key, n->factors[i].bin) & (capacity-1);
        while (slots[pos]) pos = (pos+1) & (capacity-1);
        slots[pos] = i+1;
    }
    free(n->factor_slots); n->factor_slots = slots; n->factor_slots_capacity = capacity;
    return 0;
}
static double factor(Network *n, Bus *b, double t, size_t *index, int *reused, char key[384]) {
    *index = NONE; *reused = 0; key[0] = '\0';
    if (!n->cv) return 1;
    Visit *v = &b->visits[b->current];
    int bin = (int)floor(t/300);
    if (strcmp(v->shared, "-")) snprintf(key, 384, "%s|%s", n->shared ? "" : b->route, v->shared);
    else snprintf(key, 384, "%s|%d|%d", b->route, v->stop, b->visits[b->current+1].stop);
    if (factor_table_reserve(n)) { n->error = 1; return 1; }
    size_t slot = (size_t)factor_hash(key, bin) & (n->factor_slots_capacity-1);
    while (n->factor_slots[slot]) {
        size_t i = n->factor_slots[slot]-1;
        if (n->factors[i].bin == bin && !strcmp(n->factors[i].key, key)) {
            *index = i; *reused = 1; return n->factors[i].value;
        }
        slot = (slot+1) & (n->factor_slots_capacity-1);
    }
    if (n->nf == n->cf) {
        Factor *factors = grow(n->factors, &n->cf, sizeof(Factor));
        if (!factors) { n->error = 1; return 1; }
        n->factors = factors;
    }
    double u = uniform(n, n->shared ? 3 : 2), w = uniform(n, n->shared ? 3 : 2);
    double sigma2 = log1p(n->cv*n->cv);
    double f = exp(-sigma2/2 + sqrt(sigma2)*sqrt(-2*log(u))*cos(6.2831853071795864769*w));
    *index = n->nf;
    Factor *x = &n->factors[n->nf++]; strcpy(x->key, key); x->bin = bin; x->value = f;
    n->factor_slots[slot] = *index+1;
    return f;
}
static void csv_text(FILE *f, const char *text) {
    fputc('"', f);
    for (; *text; ++text) { if (*text == '"') fputc('"', f); fputc(*text, f); }
    fputc('"', f);
}
static void travel_record(Network *n, Bus *b, double t, double duration, double f,
                          size_t index, int reused, const char *key) {
    if (!n->travel) return;
    FILE *out = n->travel;
    Visit *v = &b->visits[b->current], *next = &b->visits[b->current+1];
    fprintf(out, "%llu,%zu,", (unsigned long long)n->replica, (size_t)(b-n->buses));
    csv_text(out, b->route); fputc(',', out); csv_text(out, b->direction); fputc(',', out);
    csv_text(out, b->trip);
    fprintf(out, ",%d,%d,%d,%d,", v->sequence, next->sequence, v->stop, next->stop);
    csv_text(out, v->shared);
    fprintf(out, ",%.17g,%.17g,%.17g,%.17g,%.17g,%d,", t, t+duration, v->travel, duration, f, (int)floor(t/300));
    csv_text(out, key);
    if (index == NONE) fputs(",-1", out); else fprintf(out, ",%zu", index);
    fprintf(out, ",%d,%d,%.17g,%d\n", reused, n->shared, n->cv, t+duration < n->end);
    if (ferror(out)) n->error = 1;
}
static void visit(Network *n, Bus *b, double t) {
    int qi = b->visits[b->current].queue;
    if (qi >= 0) {
        Queue *q = &n->queues[qi];
        if (q->last_bus >= n->start) {
            double h = t-q->last_bus; ++q->hw_n; q->hw_sum += h; q->hw_square += h*h;
        }
        q->last_bus = t;
    }
}
static void dispatch(Network *n, PmEvent e) {
    double t = e.time;
    if (e.kind == N_FIXED) {
        size_t qi = n->people[e.payload].queue;
        ++n->queues[qi].arrivals; enqueue(n, qi, e.payload, t); return;
    }
    if (e.kind == N_ARRIVE) {
        Queue *q = &n->queues[e.payload];
        size_t d = (size_t)(uniform(n, 1)*(double)q->nd);
        Person p = {NONE, e.payload, NONE, q->destinations[d], WAITING, 0, 0, e.passenger, t, NAN};
        size_t pi = person_new(n, p); if (n->error) return;
        ++q->arrivals; enqueue(n, e.payload, pi, t); next_arrival(n, e.payload, t); return;
    }
    if (e.kind == N_SAMPLE) {
        for (size_t q = 0; q < n->nq; ++q) {
            integrate(n, &n->queues[q], t);
            record(n, t, "queue_primary", NONE, q, NONE, (double)n->queues[q].waiting[0]);
            record(n, t, "queue_initial", NONE, q, NONE, (double)n->queues[q].waiting[1]);
            record(n, t, "area_primary", NONE, q, NONE, n->queues[q].area[0]);
            record(n, t, "area_initial", NONE, q, NONE, n->queues[q].area[1]);
            record(n, t, "boarded_primary", NONE, q, NONE, (double)n->queues[q].boarded);
            record(n, t, "arrivals_primary", NONE, q, NONE, (double)n->queues[q].arrivals);
        }
        for (size_t b = 0; b < n->nb; ++b)
            if (n->buses[b].active) record(n, t, "occupancy", b, NONE, NONE, (double)n->buses[b].occupancy);
        event(n, t+300, N_SAMPLE, 0, 0); return;
    }
    Bus *b = &n->buses[e.payload];
    b->phase = (int)e.kind;
    if (e.kind == N_ORIGIN) {
        b->active = 1; visit(n, b, t);
        size_t pi;
        while (b->occupancy < b->capacity && (pi = eligible(n, b)) != NONE) board(n, b, pi, t);
        if (b->occupancy == b->capacity) deny(n, b);
        event(n, t, N_LEG, e.payload, 0);
    } else if (e.kind == N_BUS) {
        b->active = 1; visit(n, b, t);
        record(n, t, "visit", e.payload, NONE, NONE, (double)b->current);
        if (alighter(n, b) != NONE || eligible(n, b) != NONE) { b->phase = N_OPEN; event(n, t+2, N_OPEN, e.payload, 0); }
        else if (b->current+1 == b->nv) b->active = 0;
        else event(n, t, N_LEG, e.payload, 0);
    } else if (e.kind == N_OPEN) event(n, t, N_DECIDE, e.payload, 0);
    else if (e.kind == N_DECIDE) {
        size_t pi = alighter(n, b);
        if (pi != NONE) { b->phase = N_ALIGHT; b->serving = pi; event(n, t+1, N_ALIGHT, e.payload, n->people[pi].id); }
        else if (b->current+1 == b->nv) b->active = 0;
        else if (b->occupancy < b->capacity && (pi = eligible(n, b)) != NONE) {
            b->serving = pi; n->people[pi].state = RESERVED;
            b->phase = N_BOARD;
            event(n, t+2, N_BOARD, e.payload, n->people[pi].id);
        } else {
            if (b->occupancy == b->capacity) deny(n, b);
            b->phase = N_CLOSE;
            event(n, t+3, N_CLOSE, e.payload, 0);
        }
    } else if (e.kind == N_ALIGHT) {
        size_t pi = b->serving, previous = NONE, current = b->head;
        while (current != NONE && current != pi) { previous = current; current = n->people[current].next; }
        if (current == NONE || !b->occupancy) { n->error = 1; return; }
        Person *p = &n->people[pi];
        if (previous == NONE) b->head = p->next; else n->people[previous].next = p->next;
        if (b->tail == pi) b->tail = previous;
        b->occupancy_area += (t-b->occupancy_last)*(double)b->occupancy; b->occupancy_last = t;
        --b->occupancy; p->state = FINISHED; b->serving = NONE;
        if (p->cohort) ++n->initial_completed;
        else ++n->completed;
        if (isfinite(p->boarded)) { n->ride_sum += t-p->boarded; ++n->ride_n; }
        event(n, t, N_DECIDE, e.payload, 0);
    } else if (e.kind == N_BOARD) {
        board(n, b, b->serving, t); b->serving = NONE; event(n, t, N_DECIDE, e.payload, 0);
    } else if (e.kind == N_CLOSE) event(n, t, N_LEG, e.payload, 0);
    else if (e.kind == N_LEG) {
        size_t index; int reused; char key[384];
        double f = factor(n, b, t, &index, &reused, key);
        record(n, t, "travel_factor", e.payload, NONE, NONE, f);
        double travel = b->visits[b->current].travel*f;
        if (!(travel > 0) || t+travel <= t) { n->error = 1; return; }
        travel_record(n, b, t, travel, f, index, reused, key);
        ++b->current; event(n, t+travel, N_BUS, e.payload, 0);
    }
}

static int load(Network *n, FILE *f) {
    char magic[16];
    if (fscanf(f, "%15s %lf %lf %lf %d", magic, &n->start, &n->end, &n->cv, &n->shared) != 5 ||
        strcmp(magic, "PMNET1") || !isfinite(n->start) || !isfinite(n->end) || n->start < 0 || n->end <= n->start ||
        n->end > 1e9 || n->end-n->start > 14400 || !isfinite(n->cv) || n->cv < 0 || n->cv > 10 || (n->shared != 0 && n->shared != 1)) return -1;
    if (fscanf(f, "%zu %zu", &n->nq, &n->nb) != 2 || n->nq > MAX_OBJECTS || n->nb > MAX_OBJECTS || !n->nb) return -1;
    n->queues = calloc(n->nq ? n->nq : 1, sizeof(Queue)); n->buses = calloc(n->nb, sizeof(Bus));
    if (!n->queues || !n->buses) return -1;
    for (size_t i = 0; i < n->nq; ++i) {
        Queue *q = &n->queues[i]; q->head = q->tail = NONE; q->last = n->start; q->last_bus = -1;
        if (fscanf(f, "%95s %95s %d %zu", q->route, q->direction, &q->stop, &q->nd) != 4 || !q->nd || q->nd > MAX_VISITS || q->stop < 0) return -1;
        for (size_t d = 0; d < q->nd; ++d) if (fscanf(f, "%d", &q->destinations[d]) != 1 || q->destinations[d] < 0) return -1;
        for (int j = 0; j < 8; ++j) if (fscanf(f, "%lf", &q->rates[j]) != 1 || !isfinite(q->rates[j]) || q->rates[j] < 0) return -1;
        for (size_t j = 0; j < i; ++j)
            if (q->stop == n->queues[j].stop && !strcmp(q->route, n->queues[j].route) && !strcmp(q->direction, n->queues[j].direction)) return -1;
    }
    for (size_t i = 0; i < n->nb; ++i) {
        Bus *b = &n->buses[i]; b->head = b->tail = b->serving = NONE; b->occupancy_last = n->start;
        if (fscanf(f, "%95s %95s %95s %zu %zu %zu %lf %d", b->route, b->direction, b->trip,
            &b->capacity, &b->nv, &b->current, &b->first_time, &b->origin) != 8 ||
            !b->capacity || b->capacity > 10000 || b->nv < 2 || b->nv > MAX_VISITS || b->current >= b->nv ||
            !isfinite(b->first_time) || b->first_time < n->start || (b->origin != 0 && b->origin != 1) || (b->origin && b->current)) return -1;
        b->visits = calloc(b->nv, sizeof(Visit)); if (!b->visits) return -1;
        for (size_t j = 0; j < b->nv; ++j) {
            Visit *v = &b->visits[j]; v->queue = -1;
            if (fscanf(f, "%d %d %d %d %lf %95s", &v->stop, &v->sequence, &v->pickup, &v->dropoff, &v->travel, v->shared) != 6 ||
                v->stop < 0 || v->sequence < 0 || (j && v->sequence <= b->visits[j-1].sequence) ||
                (v->pickup != 0 && v->pickup != 1) || (v->dropoff != 0 && v->dropoff != 1) ||
                !isfinite(v->travel) || (j+1 < b->nv && v->travel <= 0)) return -1;
            for (size_t q = 0; q < n->nq; ++q) if (n->queues[q].stop == v->stop &&
                !strcmp(n->queues[q].route, b->route) && !strcmp(n->queues[q].direction, b->direction)) v->queue = (int)q;
        }
        for (size_t j = 0; j < i; ++j) if (!strcmp(b->trip, n->buses[j].trip)) return -1;
        b->active = !b->origin;
        event(n, b->first_time, b->origin ? N_ORIGIN : N_BUS, i, 0);
    }
    size_t count;
    if (fscanf(f, "%zu", &count) != 1 || count > 1000000) return -1;
    for (size_t i = 0; i < count; ++i) {
        int onboard, dest; size_t owner, vi; double arrival;
        if (fscanf(f, "%d %zu %d %zu %lf", &onboard, &owner, &dest, &vi, &arrival) != 5 ||
            !isfinite(arrival) || arrival > n->start || dest < 0 || (onboard != 0 && onboard != 1)) return -1;
        Person p = {NONE, NONE, vi, dest, onboard ? ONBOARD : WAITING, 1, 0, (UINT64_C(1) << 63) | (uint64_t)i, arrival, NAN};
        if (onboard) {
            if (owner >= n->nb) return -1;
            Bus *b = &n->buses[owner];
            if (b->origin || vi < b->current || vi >= b->nv || b->visits[vi].stop != dest ||
                !b->visits[vi].dropoff || b->occupancy >= b->capacity) return -1;
            size_t pi = person_new(n, p); if (n->error) return -1;
            if (b->tail != NONE) n->people[b->tail].next = pi; else b->head = pi;
            b->tail = pi; ++b->occupancy; ++n->initial_onboard;
        } else {
            if (owner >= n->nq) return -1;
            Queue *q = &n->queues[owner]; int supported = 0;
            for (size_t d = 0; d < q->nd; ++d) if (q->destinations[d] == dest) supported = 1;
            if (!supported || (q->tail != NONE && n->people[q->tail].arrival > arrival)) return -1;
            p.queue = owner; size_t pi = person_new(n, p); if (n->error) return -1;
            ++q->initial; enqueue(n, owner, pi, n->start);
        }
    }
    /* Optional deterministic arrivals for verification fixtures. */
    char extra[2];
    if (fscanf(f, "%1s", extra) == 1) {
        if (strcmp(extra, "D") || fscanf(f, "%zu", &count) != 1 || count > 1000000) return -1;
        for (size_t i = 0; i < count; ++i) {
            size_t qi; int dest; double t;
            if (fscanf(f, "%zu %d %lf", &qi, &dest, &t) != 3 || qi >= n->nq ||
                !isfinite(t) || t < n->start || t > n->end) return -1;
            int supported = 0;
            for (size_t d = 0; d < n->queues[qi].nd; ++d) if (n->queues[qi].destinations[d] == dest) supported = 1;
            if (!supported) return -1;
            Person p = {NONE, qi, NONE, dest, WAITING, 0, 0, ((uint64_t)qi << 32) | ++n->queues[qi].local_id, t, NAN};
            size_t pi = person_new(n, p); if (n->error) return -1;
            event(n, t, N_FIXED, pi, p.id);
        }
        if (fscanf(f, "%1s", extra) == 1) return -1;
    }
    if (ferror(f)) return -1;
    return n->error ? -1 : 0;
}

static void rng_json(FILE *f, PmRng *rng) {
    fputc('[', f);
    for (unsigned i = 0; i < 4; ++i) {
        fprintf(f, "%s{\"stream\":%u,\"state\":%u,\"offset\":%llu,\"limit\":%llu,\"draws\":%llu}",
                i ? "," : "", i, (unsigned)rng->state[i],
                (unsigned long long)pm_rng_network_offset(i),
                (unsigned long long)pm_rng_limit(rng, i), (unsigned long long)rng->draws[i]);
    }
    fputc(']', f);
}
static int summary(Network *n, FILE *out, PmRng *initial) {
    uint64_t arrived = 0, boarded = 0, waiting = 0, onboard = 0, reserved = 0, initial_waiting = 0;
    double area = 0, wait = 0;
    for (size_t i = 0; i < n->nq; ++i) {
        Queue *q = &n->queues[i]; integrate(n, q, n->end);
        if (q->arrivals != q->boarded + q->waiting[0] || q->initial != q->initial_boarded + q->waiting[1]) return -1;
        arrived += q->arrivals; boarded += q->boarded; waiting += q->waiting[0]; initial_waiting += q->waiting[1];
        area += q->area[0]; wait += q->wait_sum;
        for (size_t p = q->head; p != NONE; p = n->people[p].next) {
            if (!n->people[p].cohort) wait += n->end-n->people[p].arrival;
            if (n->people[p].state == RESERVED) ++reserved;
        }
    }
    uint64_t primary_onboard = 0, initial_boarded = n->initial_onboard;
    double occupancy_area = 0;
    for (size_t i = 0; i < n->nq; ++i) initial_boarded += n->queues[i].initial_boarded;
    for (size_t b = 0; b < n->nb; ++b) {
        size_t reservation = n->buses[b].serving != NONE && n->people[n->buses[b].serving].state == RESERVED;
        if (n->buses[b].occupancy+reservation > n->buses[b].capacity) return -1;
        onboard += n->buses[b].occupancy;
        n->buses[b].occupancy_area += (n->end-n->buses[b].occupancy_last)*(double)n->buses[b].occupancy;
        occupancy_area += n->buses[b].occupancy_area;
        for (size_t p = n->buses[b].head; p != NONE; p = n->people[p].next) if (!n->people[p].cohort) ++primary_onboard;
    }
    if (boarded != primary_onboard+n->completed || initial_boarded != onboard-primary_onboard+n->initial_completed ||
        fabs(area-wait) > 1e-7*fmax(1, area)) return -1;
    fprintf(out, "{\"model\":\"network\",\"rng_version\":\"lehmer48271-m2147483647-network-partition-v2\",\"status\":\"verification_run_not_empirically_validated\","
            "\"root_seed\":%u,\"replica\":%llu,"
            "\"start\":%.17g,\"end\":%.17g,\"arrivals\":%llu,\"boarded\":%llu,\"unserved\":%llu,"
            "\"onboard\":%llu,\"reserved\":%llu,\"initial_waiting\":%llu,\"completed\":%llu,"
            "\"queue_area\":%.17g,\"restricted_wait_sum\":%.17g,\"mean_wait\":",
            (unsigned)n->rng->root_seed, (unsigned long long)n->replica, n->start, n->end,
            (unsigned long long)arrived, (unsigned long long)boarded, (unsigned long long)waiting,
            (unsigned long long)onboard, (unsigned long long)reserved, (unsigned long long)initial_waiting,
            (unsigned long long)n->completed, area, wait);
    if (arrived) fprintf(out, "%.17g", wait/(double)arrived); else fputs("null", out);
    fprintf(out, ",\"completed_rides_with_known_boarding\":%llu,\"completed_ride_time_sum\":%.17g,"
            "\"primary_onboard\":%llu,\"initial_onboard\":%llu,\"initial_completed\":%llu,\"occupancy_area\":%.17g,\"queues\":[",
            (unsigned long long)n->ride_n, n->ride_sum, (unsigned long long)primary_onboard,
            (unsigned long long)(onboard-primary_onboard), (unsigned long long)n->initial_completed, occupancy_area);
    for (size_t i = 0; i < n->nq; ++i) {
        Queue *q = &n->queues[i];
        fprintf(out, "%s{\"index\":%zu,\"arrivals\":%llu,\"boarded\":%llu,\"waiting\":%llu,"
                "\"initial_waiting\":%llu,\"initial_boarded\":%llu,\"area\":%.17g,\"initial_area\":%.17g,\"denied_events\":%llu,"
                "\"denied_passengers\":%llu,\"headways\":%llu,\"headway_sum\":%.17g,\"headway_square_sum\":%.17g}",
                i ? "," : "", i, (unsigned long long)q->arrivals, (unsigned long long)q->boarded,
                (unsigned long long)q->waiting[0], (unsigned long long)q->waiting[1], (unsigned long long)q->initial_boarded, q->area[0], q->area[1],
                (unsigned long long)q->denied, (unsigned long long)q->denied_people, (unsigned long long)q->hw_n, q->hw_sum, q->hw_square);
    }
    fputs("],\"buses\":[", out);
    for (size_t i = 0; i < n->nb; ++i) {
        Bus *b = &n->buses[i];
        fprintf(out, "%s{\"index\":%zu,\"visit\":%zu,\"active\":%d,\"phase\":%d,\"occupancy\":%zu,\"capacity\":%zu,\"occupancy_area\":%.17g}",
                i ? "," : "", i, b->current, b->active, b->phase, b->occupancy, b->capacity, b->occupancy_area);
    }
    fprintf(out, "],\"environment_keys\":%zu,\"rng_initial\":", n->nf); rng_json(out, initial);
    fputs(",\"rng_final\":", out); rng_json(out, n->rng); fputs("}\n", out);
    return ferror(out) ? -1 : 0;
}

int pm_network_run(const char *path, PmRng *rng, uint64_t replica, FILE *out, FILE *trace) {
    return pm_network_run_diagnostic(path, rng, replica, out, trace, NULL);
}

int pm_network_run_diagnostic(const char *path, PmRng *rng, uint64_t replica,
                              FILE *out, FILE *trace, FILE *travel) {
    if (!path || !rng || rng->algorithm != 1 || !out) return -1;
    Network n; memset(&n, 0, sizeof(n)); n.rng = rng; n.trace = trace; n.travel = travel;
    n.replica = replica;
    FILE *f = fopen(path, "rb"); if (!f) return -1;
    PmRng initial = *rng;
    int rc = load(&n, f); fclose(f);
    if (rc) goto done;
    if (travel && ftell(travel) == 0 && fprintf(travel,
        "replica,bus,route_id,direction_id,trip_id,from_sequence,to_sequence,from_stop,to_stop,shared_arc,departure,arrival,reference,duration,factor,environment_bin,environment_key,factor_index,reused,shared_mode,cv,completes_before_end\n") < 0) {
        rc = -1; goto done;
    }
    if (trace && fprintf(trace, "time,type,bus,queue,person,value\n") < 0) { rc = -1; goto done; }
    for (size_t i = 0; i < n.nq; ++i) next_arrival(&n, i, n.start);
    event(&n, n.start, N_SAMPLE, 0, 0);
    PmEvent e;
    while (!n.error && pm_calendar_pop(&n.calendar, &e)) dispatch(&n, e);
    if (n.error) rc = -1;
    else {
        /* Samples at the horizon are snapshots only, never mutate the system. */
        for (size_t q = 0; q < n.nq; ++q) {
            record(&n, n.end, "queue_primary", NONE, q, NONE, (double)n.queues[q].waiting[0]);
            record(&n, n.end, "queue_initial", NONE, q, NONE, (double)n.queues[q].waiting[1]);
            integrate(&n, &n.queues[q], n.end);
            record(&n, n.end, "area_primary", NONE, q, NONE, n.queues[q].area[0]);
            record(&n, n.end, "area_initial", NONE, q, NONE, n.queues[q].area[1]);
            record(&n, n.end, "boarded_primary", NONE, q, NONE, (double)n.queues[q].boarded);
            record(&n, n.end, "arrivals_primary", NONE, q, NONE, (double)n.queues[q].arrivals);
        }
        rc = n.error ? -1 : summary(&n, out, &initial);
    }
done:
    if (n.buses) for (size_t i = 0; i < n.nb; ++i) free(n.buses[i].visits);
    free(n.buses); free(n.queues); free(n.people); free(n.factors); free(n.factor_slots); pm_calendar_destroy(&n.calendar);
    return rc;
}
