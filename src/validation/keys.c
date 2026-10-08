#include "rome_bus_pmcsn/audit.h"
#include <stdlib.h>
#include <string.h>
/* Independent key sets; exact string comparison, no numeric conversion. */
typedef struct Key { struct Key *next; char value[]; } Key;
typedef struct { Key **buckets; size_t duplicates, count; } Set;
#define BUCKETS 262144u
static size_t bucket(const char *s) {
    uint64_t h = UINT64_C(14695981039346656037);
    while (*s) { h ^= (unsigned char)*s++; h *= UINT64_C(1099511628211); }
    return (size_t)(h & (BUCKETS - 1));
}
static int contains(const Set *set, const char *s) {
    for (Key *k = set->buckets[bucket(s)]; k; k = k->next) if (!strcmp(k->value, s)) return 1;
    return 0;
}
static int add(Set *set, const char *s) {
    if (!*s) return -1;
    if (contains(set, s)) { set->duplicates++; return 0; }
    size_t n = strlen(s), b = bucket(s);
    Key *k = malloc(sizeof(*k) + n + 1); if (!k) return -1;
    memcpy(k->value, s, n + 1); k->next = set->buckets[b]; set->buckets[b] = k; set->count++; return 0;
}
static void release(Set *set) {
    if (!set->buckets) return;
    for (size_t i = 0; i < BUCKETS; ++i) { Key *k = set->buckets[i]; while (k) { Key *next = k->next; free(k); k = next; } }
    free(set->buckets);
}
static FILE *table(const char *directory, const char *name) {
    char path[4096]; int n = snprintf(path, sizeof(path), "%s/%s", directory, name);
    return n < 0 || (size_t)n >= sizeof(path) ? NULL : fopen(path, "rb");
}
static int column(char **fields, int count, const char *name) {
    for (int i = 0; i < count; ++i) if (!strcmp(fields[i], name)) return i;
    return -1;
}
static int load(const char *directory, const char *name, const char *id, Set *set, int optional) {
    FILE *f = table(directory, name); if (!f) return optional ? 0 : -1;
    char buf[65536], *fields[128]; int n = csv_row(f, buf, sizeof(buf), fields, 128);
    int key = column(fields, n, id); if (key < 0) { fclose(f); return -1; }
    int width = n;
    while ((n = csv_row(f, buf, sizeof(buf), fields, 128)) > 0) if (n != width || add(set, fields[key])) { fclose(f); return -1; }
    fclose(f); return n < 0 ? -1 : 0;
}
static int references(const char *directory, const char *name, const char **names, Set **sets, size_t count, size_t *missing) {
    FILE *f = table(directory, name); if (!f) return -1;
    char buf[65536], *fields[128]; int indexes[4];
    int n = csv_row(f, buf, sizeof(buf), fields, 128), width = n;
    if (count > 4) { fclose(f); return -1; }
    for (size_t i = 0; i < count; ++i) { indexes[i] = column(fields, n, names[i]); if (indexes[i] < 0) { fclose(f); return -1; } }
    while ((n = csv_row(f, buf, sizeof(buf), fields, 128)) > 0) {
        if (n != width) { fclose(f); return -1; }
        for (size_t i = 0; i < count; ++i) if (!contains(sets[i], fields[indexes[i]])) missing[i]++;
    }
    fclose(f); return n < 0 ? -1 : 0;
}
int validate_keys(const char *directory) {
    Set stops = {0}, routes = {0}, trips = {0}, services = {0}, shapes = {0};
    Set *all[] = {&stops, &routes, &trips, &services, &shapes}; int result = 1;
    for (size_t i = 0; i < 5; ++i) { all[i]->buckets = calloc(BUCKETS, sizeof(Key *)); if (!all[i]->buckets) goto cleanup; }
    if (load(directory, "stops.txt", "stop_id", &stops, 0) || load(directory, "routes.txt", "route_id", &routes, 0) || load(directory, "trips.txt", "trip_id", &trips, 0) || load(directory, "calendar_dates.txt", "service_id", &services, 1) || load(directory, "calendar.txt", "service_id", &services, 1) || load(directory, "shapes.txt", "shape_id", &shapes, 0) || !services.count) goto cleanup;
    const char *trip_names[] = {"route_id", "service_id", "shape_id"}; Set *trip_sets[] = {&routes, &services, &shapes}; size_t trip_missing[3] = {0};
    const char *stop_names[] = {"trip_id", "stop_id"}; Set *stop_sets[] = {&trips, &stops}; size_t stop_missing[2] = {0};
    if (references(directory, "trips.txt", trip_names, trip_sets, 3, trip_missing) || references(directory, "stop_times.txt", stop_names, stop_sets, 2, stop_missing)) goto cleanup;
    printf("duplicate_stop_ids=%zu\nduplicate_route_ids=%zu\nduplicate_trip_ids=%zu\ntrips_missing_route=%zu\ntrips_missing_service=%zu\ntrips_missing_shape=%zu\nstop_times_missing_trip=%zu\nstop_times_missing_stop=%zu\n", stops.duplicates, routes.duplicates, trips.duplicates, trip_missing[0], trip_missing[1], trip_missing[2], stop_missing[0], stop_missing[1]);
    result = stops.duplicates || routes.duplicates || trips.duplicates || trip_missing[0] || trip_missing[1] || trip_missing[2] || stop_missing[0] || stop_missing[1];
cleanup:
    for (size_t i = 0; i < 5; ++i) release(all[i]);
    if (result) fprintf(stderr, "GTFS key validation failed; see diagnostics.\n");
    return result;
}
