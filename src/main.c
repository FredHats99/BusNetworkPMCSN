#include "rome_bus_pmcsn/audit.h"
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <math.h>
#include <stdint.h>
int download_feed(const char *name, const char *path);
int validate_keys(const char *directory);
static int audit_file(const char *path, int ids) {
    FILE *f = fopen(path, "rb"); if (!f) return 1;
    if (fseek(f, 0, SEEK_END)) { fclose(f); return 1; }
    long n = ftell(f);
    if (n <= 0 || n > 64 * 1024 * 1024 || fseek(f, 0, SEEK_SET)) { fclose(f); return 1; }
    unsigned char *data = malloc((size_t)n); if (!data) { fclose(f); return 1; }
    int rc = -1;
    if (fread(data, 1, (size_t)n, f) == (size_t)n) {
        if (ids) {
            FILE *sink = tmpfile();
            if (sink) { rc = audit_feed(data, (size_t)n, sink); fclose(sink); }
            if (!rc) rc = feed_trip_ids(data, (size_t)n, stdout);
        } else rc = audit_feed(data, (size_t)n, stdout);
    }
    free(data); fclose(f); if (rc) fprintf(stderr, "Invalid/unsupported protobuf feed: %s\n", path); return rc ? 1 : 0;
}
static int audit_csv(const char *path) {
    FILE *f = fopen(path, "rb"); if (!f) return 1;
    char buffer[65536], *fields[128]; size_t rows = 0, beyond24 = 0;
    int n, columns = 0, arrival = -1, departure = -1, latitude = -1, longitude = -1, sequence = -1;
    while ((n = csv_row(f, buffer, sizeof(buffer), fields, 128)) > 0) {
        if (!columns) {
            columns = n; printf("columns=%d\n", n);
            for (int i = 0; i < n; ++i) {
                printf("%s%s", i ? "," : "", fields[i]);
                if (!strcmp(fields[i], "arrival_time")) arrival = i;
                if (!strcmp(fields[i], "departure_time")) departure = i;
                if (!strcmp(fields[i], "stop_lat") || !strcmp(fields[i], "shape_pt_lat")) latitude = i;
                if (!strcmp(fields[i], "stop_lon") || !strcmp(fields[i], "shape_pt_lon")) longitude = i;
                if (!strcmp(fields[i], "stop_sequence") || !strcmp(fields[i], "shape_pt_sequence")) sequence = i;
            }
            puts("");
        } else {
            if (n != columns) { fclose(f); fprintf(stderr, "Column mismatch at row %zu\n", rows + 1); return 1; }
            int time_columns[2] = {arrival, departure};
            for (unsigned k = 0; k < 2; ++k) if (time_columns[k] >= 0 && *fields[time_columns[k]]) {
                uint64_t seconds;
                if (gtfs_time(fields[time_columns[k]], &seconds)) { fclose(f); fprintf(stderr, "Invalid GTFS time at row %zu\n", rows + 1); return 1; }
                if (seconds >= 86400) beyond24++;
            }
            int coordinates[2] = {latitude, longitude};
            for (unsigned k = 0; k < 2; ++k) if (coordinates[k] >= 0 && *fields[coordinates[k]]) {
                char *end; errno = 0;
                double value = strtod(fields[coordinates[k]], &end);
                double limit = k ? 180 : 90;
                if (errno || *end || !isfinite(value) || value < -limit || value > limit) { fclose(f); fprintf(stderr, "Invalid coordinate at row %zu\n", rows + 1); return 1; }
            }
            if (sequence >= 0) {
                const char *p = fields[sequence];
                if (!*p) { fclose(f); return 1; }
                while (*p >= '0' && *p <= '9') p++;
                if (*p) { fclose(f); fprintf(stderr, "Invalid sequence at row %zu\n", rows + 1); return 1; }
            }
            rows++;
        }
    }
    fclose(f); if (n < 0 || !columns) return 1;
    printf("rows=%zu\ntime_values_at_or_beyond_24h=%zu\n", rows, beyond24); return 0;
}
int main(int argc, char **argv) {
    if (argc == 2 && !strcmp(argv[1], "--help")) {
        puts("rome_bus_pmcsn download-static OUTPUT.zip\nrome_bus_pmcsn download-feed vehicles|updates|alerts OUTPUT.pb\nrome_bus_pmcsn audit-feeds FILE.pb\nrome_bus_pmcsn feed-trip-ids FILE.pb\nrome_bus_pmcsn audit-static FILE.txt\nPhase 0: structural and scalar audit; relational validation remains separate."); return 0;
    }
    if (argc == 3 && !strcmp(argv[1], "download-static")) return download_feed("static", argv[2]);
    if (argc == 4 && !strcmp(argv[1], "download-feed")) return download_feed(argv[2], argv[3]);
    if (argc == 3 && !strcmp(argv[1], "audit-feeds")) return audit_file(argv[2], 0);
    if (argc == 3 && !strcmp(argv[1], "feed-trip-ids")) return audit_file(argv[2], 1);
    if (argc == 3 && !strcmp(argv[1], "audit-static")) return audit_csv(argv[2]);
    if (argc == 3 && !strcmp(argv[1], "validate-keys")) return validate_keys(argv[2]);
    fprintf(stderr, "Unsupported arguments. Use --help.\n"); return 2;
}
