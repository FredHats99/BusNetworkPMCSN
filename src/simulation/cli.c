#include "rome_bus_pmcsn/simulation.h"
#include <errno.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>
#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#include <sys/stat.h>
#endif

static FILE *new_file(const char *path) {
#ifdef _WIN32
    /* The Windows CRT used by MinGW does not implement fopen's C11 x mode. */
    int fd = _open(path, _O_WRONLY | _O_CREAT | _O_EXCL | _O_TEXT, _S_IREAD | _S_IWRITE);
    if (fd < 0) return NULL;
    FILE *f = _fdopen(fd, "w");
    if (!f) _close(fd);
    return f;
#else
    return fopen(path, "wx");
#endif
}

static int real_value(const char *s, double *out) {
    char *end; errno = 0; double n = strtod(s, &end);
    if (!*s || *end || errno || !isfinite(n)) return -1;
    *out = n; return 0;
}
static int integer_value(const char *s, uint64_t *out) {
    if (!*s) return -1;
    for (const char *p = s; *p; ++p) if (*p < '0' || *p > '9') return -1;
    char *end; errno = 0; unsigned long long n = strtoull(s, &end, 10);
    if (errno || *end) return -1;
    *out = (uint64_t)n; return 0;
}
/* Replica-boundary RNG checkpoints, not snapshots of passengers/calendar. */
static int load_checkpoint(const char *path, PmRng *rng) {
    FILE *f = fopen(path, "rb"); if (!f) return -1;
    PmRng candidate;
    char line[512], magic[32], seed_text[32], extra;
    uint64_t seed; int rc = -1;
    if (!fgets(line, sizeof(line), f) ||
        sscanf(line, "%31s %31s %c", magic, seed_text, &extra) != 2 ||
        strcmp(magic, "PMLEHMER2") || integer_value(seed_text, &seed) ||
        !seed || seed >= UINT64_C(2147483647) || pm_rng_init_network(&candidate, (uint32_t)seed)) goto done;
    for (unsigned i = 0; i < 4; ++i) {
        uint64_t values[5];
        if (!fgets(line, sizeof(line), f)) goto done;
        char *token = strtok(line, " \t\r\n");
        for (unsigned j = 0; j < 5; ++j) {
            if (!token || integer_value(token, &values[j])) goto done;
            token = strtok(NULL, " \t\r\n");
        }
        if (token || values[0] != i || values[2] != pm_rng_network_offset(i) ||
            values[3] != pm_rng_limit(&candidate, i) ||
            pm_rng_advance(&candidate, i, values[4]) || values[1] != candidate.state[i]) goto done;
    }
    if (!fgets(line, sizeof(line), f) || (strcmp(line, "END\n") && strcmp(line, "END\r\n") && strcmp(line, "END"))) goto done;
    int c;
    while ((c = fgetc(f)) != EOF) if (c != ' ' && c != '\t' && c != '\r' && c != '\n') goto done;
    if (ferror(f)) goto done;
    *rng = candidate; rc = 0;
done:
    fclose(f); return rc;
}
static int save_checkpoint(FILE *f, const PmRng *rng) {
    fprintf(f, "PMLEHMER2 %u\n", (unsigned)rng->root_seed);
    for (unsigned i = 0; i < 4; ++i)
        fprintf(f, "%u %u %llu %llu %llu\n", i, (unsigned)rng->state[i],
                (unsigned long long)pm_rng_network_offset(i),
                (unsigned long long)pm_rng_limit(rng, i), (unsigned long long)rng->draws[i]);
    fputs("END\n", f);
    return ferror(f) ? -1 : 0;
}
static int parse_ceilings(const char *text, uint64_t values[4]) {
    char buffer[128];
    if (strlen(text) >= sizeof(buffer)) return -1;
    strcpy(buffer, text);
    char *start = buffer;
    for (unsigned i = 0; i < 4; ++i) {
        char *comma = strchr(start, ',');
        if ((i < 3) != (comma != NULL)) return -1;
        if (comma) *comma = '\0';
        if (integer_value(start, &values[i])) return -1;
        if (comma) start = comma+1;
    }
    return 0;
}
static void states(FILE *f, const PmRng *r) {
    fputc('[', f);
    for (unsigned i = 0; i < PMCSN_STREAMS; ++i)
        fprintf(f, "%s{\"stream\":%u,\"state\":%u,\"draws\":%llu}", i ? "," : "", i,
                (unsigned)r->state[i], (unsigned long long)r->draws[i]);
    fputc(']', f);
}
static int validate(void) {
    PmRng rng;
    double u = 0;
    if (pm_rng_init(&rng, 1)) return 1;
    for (unsigned i = 0; i < 10000; ++i) if (pm_rng_uniform(&rng, 0, &u)) return 1;
    if (rng.state[0] != UINT32_C(399268537)) return 1;
    const double times[] = {1, 2, 3, 10, 11, 20};
    const PmControlledConfig c = {20, 10, 0, 2};
    PmControlledResult r;
    if (pm_controlled_run(&c, times, 6, &r, NULL) || r.arrivals != 5 ||
        r.boarded != 2 || r.residual != 3 || r.denied_events != 2 ||
        r.denied_passengers != 2 || fabs(r.queue_area-53) > 1e-10) return 1;
    puts("{\"controlled_deterministic\":\"passed\",\"rng_test_random\":\"passed\","
         "\"network_gate\":\"separate\",\"empirical_validation\":\"unavailable\"}");
    return 0;
}

/* A diagnostic-only batch: one RNG initialization and a fixed skipped prefix.
 * Paths are one full line each, permitting spaces. Production planning is separate. */
static int diagnostic_campaign(const char *plan_path, const char *travel_path) {
    FILE *plan = fopen(plan_path, "rb"); if (!plan) return 1;
    char magic[16]; size_t cases, replicas; uint64_t skip;
    int rc = 1;
    if (fscanf(plan, "%15s %zu %zu %" SCNu64, magic, &cases, &replicas, &skip) != 4 ||
        strcmp(magic, "PMDIAG1") || !cases || cases > 64 || !replicas || replicas > 4096 || skip > UINT64_C(100000000)) {
        fclose(plan); return 2;
    }
    int c;
    do { c = fgetc(plan); } while (c != '\n' && c != EOF);
    char (*paths)[4096] = calloc(cases, sizeof(*paths));
    if (!paths) { fclose(plan); return 1; }
    for (size_t i = 0; i < cases; ++i) {
        if (!fgets(paths[i], sizeof(paths[i]), plan)) goto done;
        size_t len = strlen(paths[i]);
        if (!len || (paths[i][len-1] != '\n' && !feof(plan))) goto done;
        while (len && (paths[i][len-1] == '\n' || paths[i][len-1] == '\r')) paths[i][--len] = '\0';
        if (!len) goto done;
    }
    do { c = fgetc(plan); } while (c == '\n' || c == '\r');
    if (c != EOF || ferror(plan)) goto done;
    PmRng rng;
    if (pm_rng_init_network(&rng, 123456789)) goto done;
    for (unsigned stream = 0; stream < 4; ++stream)
        if (pm_rng_advance(&rng, stream, skip)) goto done;
    FILE *travel = new_file(travel_path);
    if (!travel) goto done;
    if (setvbuf(travel, NULL, _IOFBF, 1024*1024) || setvbuf(stdout, NULL, _IOFBF, 1024*1024)) {
        fclose(travel); goto done;
    }
    rc = 0;
    for (size_t i = 0; i < cases && !rc; ++i) {
        for (size_t j = 0; j < replicas; ++j) {
            uint64_t replica = (uint64_t)i*replicas+j;
            if (pm_network_run_diagnostic(paths[i], &rng, replica, stdout, NULL, travel)) { rc = 1; break; }
            fprintf(stderr, "diagnostic case=%zu replica=%zu completed\n", i, j);
        }
    }
    if (fclose(travel)) rc = 1;
done:
    free(paths); fclose(plan);
    if (rc) fprintf(stderr, "Diagnostic campaign failed; partial files do not satisfy the gate.\n");
    return rc;
}

int pm_simulation_cli(int argc, char **argv) {
    if (argc == 6 && !strcmp(argv[1], "diagnose") && !strcmp(argv[2], "network") && !strcmp(argv[4], "--travel-trace"))
        return diagnostic_campaign(argv[3], argv[5]);
    if (argc == 3 && !strcmp(argv[1], "validate") && !strcmp(argv[2], "controlled")) return validate();
    if (argc >= 4 && (!strcmp(argv[1], "simulate") || !strcmp(argv[1], "validate")) && !strcmp(argv[2], "network")) {
        uint64_t seed = 123456789, replicas = 1; unsigned seen = 0;
        const char *trace_path = NULL, *travel_path = NULL, *checkpoint_in = NULL, *checkpoint_out = NULL;
        uint64_t ceilings[4];
        for (int i = 4; i < argc; i += 2) {
            if (i+1 == argc) return 2;
            unsigned bit;
            if (!strcmp(argv[i], "--seed")) { bit = 1; if (integer_value(argv[i+1], &seed)) return 2; }
            else if (!strcmp(argv[i], "--replicas")) { bit = 2; if (integer_value(argv[i+1], &replicas)) return 2; }
            else if (!strcmp(argv[i], "--trace")) { bit = 4; trace_path = argv[i+1]; }
            else if (!strcmp(argv[i], "--travel-trace")) { bit = 8; travel_path = argv[i+1]; }
            else if (!strcmp(argv[i], "--rng-checkpoint-in")) { bit = 16; checkpoint_in = argv[i+1]; }
            else if (!strcmp(argv[i], "--rng-checkpoint-out")) { bit = 32; checkpoint_out = argv[i+1]; }
            else if (!strcmp(argv[i], "--rng-draw-ceilings")) { bit = 64; if (parse_ceilings(argv[i+1], ceilings)) return 2; }
            else return 2;
            if (seen & bit) return 2;
            seen |= bit;
        }
        if (!replicas || seed == 0 || seed >= UINT64_C(2147483647) || (trace_path && replicas != 1) ||
            (checkpoint_in && (seen & 1))) return 2;
        PmRng rng;
        if (checkpoint_in ? load_checkpoint(checkpoint_in, &rng) : pm_rng_init_network(&rng, (uint32_t)seed)) {
            fprintf(stderr, "Invalid RNG checkpoint or seed.\n"); return 1;
        }
        if ((seen & 64) && pm_rng_set_ceiling(&rng, ceilings)) return 2;
        FILE *checkpoint = checkpoint_out ? new_file(checkpoint_out) : NULL;
        if (checkpoint_out && !checkpoint) return 1;
        FILE *trace = trace_path ? new_file(trace_path) : NULL;
        if (trace_path && !trace) { if (checkpoint) fclose(checkpoint); return 1; }
        FILE *travel = travel_path ? new_file(travel_path) : NULL;
        if (travel_path && !travel) { if (trace) fclose(trace); if (checkpoint) fclose(checkpoint); return 1; }
        int rc = 0;
        for (uint64_t i = 0; i < replicas; ++i) {
            if (pm_network_run_diagnostic(argv[3], &rng, i, stdout, trace, travel)) {
                fprintf(stderr, "Network verification failed: input, invariant, I/O, memory or RNG budget.\n");
                rc = 1; break;
            }
        }
        if (trace && fclose(trace)) rc = 1;
        if (travel && fclose(travel)) rc = 1;
        if (fflush(stdout)) rc = 1;
        if (checkpoint) {
            if (!rc && save_checkpoint(checkpoint, &rng)) rc = 1;
            if (fclose(checkpoint)) rc = 1;
        }
        return rc;
    }
    if (argc < 4 || strcmp(argv[1], "simulate") || strcmp(argv[2], "controlled")) return 2;
    PmControlledConfig c = {0};
    uint64_t seed = 123456789, replicas = 1, capacity = 0;
    unsigned seen = 0;
    const char *trace_path = NULL;
    for (int i = 3; i < argc; i += 2) {
        if (i+1 == argc) return 2;
        unsigned bit;
        if (!strcmp(argv[i], "--rate")) {
            bit = 1; if (real_value(argv[i+1], &c.rate)) return 2;
        } else if (!strcmp(argv[i], "--headway")) {
            bit = 2; if (real_value(argv[i+1], &c.headway)) return 2;
        } else if (!strcmp(argv[i], "--capacity")) {
            bit = 4; if (integer_value(argv[i+1], &capacity)) return 2;
        } else if (!strcmp(argv[i], "--horizon")) {
            bit = 8; if (real_value(argv[i+1], &c.horizon)) return 2;
        } else if (!strcmp(argv[i], "--seed")) {
            bit = 16; if (integer_value(argv[i+1], &seed)) return 2;
        } else if (!strcmp(argv[i], "--replicas")) {
            bit = 32; if (integer_value(argv[i+1], &replicas)) return 2;
        } else if (!strcmp(argv[i], "--trace")) {
            bit = 64; trace_path = argv[i+1];
        } else return 2;
        if (seen & bit) return 2;
        seen |= bit;
    }
    if ((seen & 15) != 15 || !capacity || capacity > SIZE_MAX || !replicas ||
        seed == 0 || seed >= UINT64_C(2147483647) || c.rate < 0 ||
        c.headway <= 0 || c.horizon <= 0 || (trace_path && replicas != 1)) return 2;
    c.capacity = (size_t)capacity;
    FILE *trace = NULL;
    if (trace_path) {
        trace = new_file(trace_path);
        if (!trace) { fprintf(stderr, "Cannot create new trace: %s\n", trace_path); return 1; }
    }
    PmRng rng;
    if (pm_rng_init(&rng, (uint32_t)seed)) { if (trace) fclose(trace); return 1; }
    int rc = 0;
    for (uint64_t i = 0; i < replicas; ++i) {
        PmRng initial = rng;
        PmControlledResult r;
        if (pm_controlled_random(&c, &rng, &r, trace)) {
            fprintf(stderr, "Controlled simulation failed (input, memory, numeric resolution or RNG budget).\n");
            rc = 1; break;
        }
        fprintf(stdout, "{\"model\":\"controlled\",\"phase\":\"verification\",\"replica\":%llu,"
                "\"rng_version\":\"lehmer48271-m2147483647-j22925-v1\",\"root_seed\":%llu,"
                "\"horizon\":%.17g,\"headway\":%.17g,\"rate\":%.17g,\"capacity\":%llu,"
                "\"arrivals\":%llu,\"boarded\":%llu,\"residual\":%llu,\"buses\":%llu,"
                "\"denied_events\":%llu,\"denied_passengers\":%llu,\"queue_area\":%.17g,"
                "\"wait_sum\":%.17g,\"mean_queue\":%.17g,\"mean_wait\":",
                (unsigned long long)i, (unsigned long long)seed, c.horizon, c.headway, c.rate,
                (unsigned long long)capacity, (unsigned long long)r.arrivals,
                (unsigned long long)r.boarded, (unsigned long long)r.residual,
                (unsigned long long)r.buses, (unsigned long long)r.denied_events,
                (unsigned long long)r.denied_passengers, r.queue_area, r.wait_sum, r.mean_queue);
        if (r.arrivals) fprintf(stdout, "%.17g", r.mean_wait); else fputs("null", stdout);
        fputs(",\"rng_initial\":", stdout); states(stdout, &initial);
        fputs(",\"rng_final\":", stdout); states(stdout, &rng);
        fputs("}\n", stdout);
        if (ferror(stdout)) { rc = 1; break; }
    }
    if (trace && fclose(trace)) rc = 1;
    return rc;
}
