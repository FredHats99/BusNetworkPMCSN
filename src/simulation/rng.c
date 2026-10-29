#include "rome_bus_pmcsn/simulation.h"
#include <string.h>

/* Lehmer, as in course lectures 16/17. Network blocks partition one period;
 * jumps change the initial position, never the recurrence or multiplier. */
static const uint64_t offsets[4] = {0, 800000000, 1600000000, 1900000000};
static const uint64_t lengths[4] = {800000000, 800000000, 300000000, 247483646};

static uint32_t power(uint64_t exponent) {
    uint64_t result = 1, base = 48271;
    while (exponent) {
        if (exponent & 1) result = result*base % UINT64_C(2147483647);
        base = base*base % UINT64_C(2147483647);
        exponent >>= 1;
    }
    return (uint32_t)result;
}
uint64_t pm_rng_network_offset(unsigned stream) {
    return stream < 4 ? offsets[stream] : 0;
}
uint64_t pm_rng_limit(const PmRng *rng, unsigned stream) {
    if (!rng || rng->algorithm > 1 || stream >= (rng->algorithm ? 4u : PMCSN_STREAMS)) return 0;
    return (rng->algorithm ? lengths[stream] : PMCSN_STREAM_SPACING)-1;
}
int pm_rng_init_network(PmRng *rng, uint32_t seed) {
    if (!rng || !seed || seed >= UINT32_C(2147483647)) return -1;
    memset(rng, 0, sizeof(*rng)); rng->algorithm = 1; rng->root_seed = seed;
    for (unsigned s = 0; s < 4; ++s) {
        rng->state[s] = (uint32_t)((uint64_t)power(offsets[s])*seed % UINT64_C(2147483647));
        rng->ceiling[s] = lengths[s]-1;
    }
    return 0;
}
int pm_rng_init(PmRng *rng, uint32_t seed) {
    if (!rng || !seed || seed >= UINT32_C(2147483647)) return -1;
    memset(rng, 0, sizeof(*rng)); rng->root_seed = seed; rng->state[0] = seed;
    for (unsigned i = 1; i < PMCSN_STREAMS; ++i)
        rng->state[i] = (uint32_t)((UINT64_C(22925)*rng->state[i-1]) % UINT64_C(2147483647));
    return 0;
}
int pm_rng_set_ceiling(PmRng *rng, const uint64_t ceiling[4]) {
    if (!rng || !ceiling || rng->algorithm != 1) return -1;
    for (unsigned i = 0; i < 4; ++i)
        if (ceiling[i] < rng->draws[i] || ceiling[i] > pm_rng_limit(rng, i)) return -1;
    for (unsigned i = 0; i < 4; ++i) rng->ceiling[i] = ceiling[i];
    return 0;
}
static uint64_t effective_limit(const PmRng *rng, unsigned stream) {
    uint64_t limit = pm_rng_limit(rng, stream);
    if (limit && rng->algorithm == 1 && rng->ceiling[stream] < limit) limit = rng->ceiling[stream];
    return limit;
}
int pm_rng_advance(PmRng *rng, unsigned stream, uint64_t count) {
    uint64_t limit = effective_limit(rng, stream);
    if (!pm_rng_limit(rng, stream) || !rng->state[stream] || rng->state[stream] >= UINT32_C(2147483647) ||
        rng->draws[stream] > limit || count > limit-rng->draws[stream]) return -1;
    rng->state[stream] = (uint32_t)((uint64_t)power(count)*rng->state[stream] % UINT64_C(2147483647));
    rng->draws[stream] += count;
    return 0;
}
int pm_rng_uniform(PmRng *rng, unsigned stream, double *value) {
    uint64_t limit = effective_limit(rng, stream);
    if (!value || !limit || !rng->state[stream] || rng->state[stream] >= UINT32_C(2147483647) ||
        rng->draws[stream] >= limit) return -1;
    /* Schrage decomposition: intermediate magnitudes fit signed 32 bits. */
    int64_t t = INT64_C(48271)*(rng->state[stream] % 44488) - INT64_C(3399)*(rng->state[stream]/44488);
    rng->state[stream] = (uint32_t)(t > 0 ? t : t+INT64_C(2147483647));
    ++rng->draws[stream];
    *value = rng->state[stream]/2147483647.0;
    return 0;
}
