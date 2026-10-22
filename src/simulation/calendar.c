#include "rome_bus_pmcsn/simulation.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

static int before(const PmEvent *a, const PmEvent *b) {
    if (a->time != b->time) return a->time < b->time;
    if (a->priority != b->priority) return a->priority < b->priority;
    int c = strcmp(a->route, b->route); if (c) return c < 0;
    c = strcmp(a->direction, b->direction); if (c) return c < 0;
    c = strcmp(a->trip, b->trip); if (c) return c < 0;
    if (a->sequence != b->sequence) return a->sequence < b->sequence;
    if (a->passenger != b->passenger) return a->passenger < b->passenger;
    return a->serial < b->serial;
}

int pm_calendar_push(PmCalendar *q, PmEvent e) {
    if (!q || !isfinite(e.time) || !e.route || !e.direction || !e.trip || q->serial == UINT64_MAX) return -1;
    if (q->size == q->capacity) {
        size_t n = q->capacity ? q->capacity * 2 : 64;
        if (n < q->capacity || n > SIZE_MAX / sizeof(e)) return -1;
        PmEvent *p = realloc(q->items, n * sizeof(e));
        if (!p) return -1;
        q->items = p; q->capacity = n;
    }
    e.serial = q->serial++;
    size_t i = q->size++;
    while (i) {
        size_t parent = (i - 1) / 2;
        if (!before(&e, &q->items[parent])) break;
        q->items[i] = q->items[parent]; i = parent;
    }
    q->items[i] = e; return 0;
}

int pm_calendar_pop(PmCalendar *q, PmEvent *event) {
    if (!q || !event || !q->size) return 0;
    *event = q->items[0];
    PmEvent last = q->items[--q->size];
    size_t i = 0;
    while (i < q->size / 2) {
        size_t child = 2*i + 1;
        if (child + 1 < q->size && before(&q->items[child+1], &q->items[child])) ++child;
        if (!before(&q->items[child], &last)) break;
        q->items[i] = q->items[child]; i = child;
    }
    /* For an even heap size the last parent has only a left child. */
    if (2*i + 1 < q->size && before(&q->items[2*i+1], &last)) {
        q->items[i] = q->items[2*i+1]; i = 2*i+1;
    }
    if (q->size) q->items[i] = last;
    return 1;
}

void pm_calendar_destroy(PmCalendar *q) {
    if (q) { free(q->items); memset(q, 0, sizeof(*q)); }
}
