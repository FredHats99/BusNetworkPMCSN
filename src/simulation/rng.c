#include "rome_bus_pmcsn/simulation.h"
#include <string.h>

/* MRG32k3a recurrences and published 2^127 stream jumps: L'Ecuyer (1999),
 * L'Ecuyer et al. (2002), umontreal-simul/RngStreams. Integer C17 implementation
 * of the specified generator; no new PRNG or arbitrary per-stream seeds. */
static const uint32_t jump[2][3][3] = {
    {{2427906178u,3580155704u,949770784u},{226153695u,1230515664u,3580155704u},{1988835001u,986791581u,1230515664u}},
    {{1464411153u,277697599u,1610723613u},{32183930u,1464411153u,1022607788u},{2824425944u,32183930u,2093834863u}}
};

int pm_rng_init_network(PmRng *rng, uint32_t seed) {
    if (!rng || !seed || seed >= UINT32_C(4294944443)) return -1;
    memset(rng, 0, sizeof(*rng)); rng->algorithm = 1; rng->root_seed = seed;
    for (unsigned j = 0; j < 6; ++j) rng->mrg[0][j] = seed;
    for (unsigned s = 1; s < PMCSN_STREAMS; ++s) {
        for (unsigned c = 0; c < 2; ++c) {
            uint64_t modulus = c ? UINT64_C(4294944443) : UINT64_C(4294967087);
            for (unsigned row = 0; row < 3; ++row) {
                uint64_t total = 0;
                for (unsigned j = 0; j < 3; ++j)
                    total = (total + ((uint64_t)jump[c][row][j]*rng->mrg[s-1][3*c+j]) % modulus) % modulus;
                rng->mrg[s][3*c+row] = (uint32_t)total;
            }
        }
    }
    return 0;
}

int pm_rng_init(PmRng *rng, uint32_t seed) {
    if (!rng || seed == 0 || seed >= UINT32_C(2147483647)) return -1;
    memset(rng, 0, sizeof(*rng));
    rng->root_seed = seed;
    rng->state[0] = seed;
    for (unsigned i = 1; i < PMCSN_STREAMS; ++i)
        rng->state[i] = (uint32_t)((UINT64_C(22925) * rng->state[i-1]) % UINT64_C(2147483647));
    return 0;
}

int pm_rng_uniform(PmRng *rng, unsigned stream, double *value) {
    if (!rng || !value || stream >= PMCSN_STREAMS) return -1;
    if (rng->algorithm == 1) {
        /* Hard limit 2^64-1 draws is strictly below the 2^127 stream spacing. */
        if (rng->draws[stream] == UINT64_MAX) return -1;
        uint32_t *s = rng->mrg[stream];
        for (unsigned j = 0; j < 6; ++j)
            if (s[j] >= (j < 3 ? UINT32_C(4294967087) : UINT32_C(4294944443))) return -1;
        if (!(s[0] || s[1] || s[2]) || !(s[3] || s[4] || s[5])) return -1;
        int64_t p = (INT64_C(1403580)*s[1]-INT64_C(810728)*s[0]) % INT64_C(4294967087);
        int64_t q = (INT64_C(527612)*s[5]-INT64_C(1370589)*s[3]) % INT64_C(4294944443);
        if (p < 0) p += INT64_C(4294967087);
        if (q < 0) q += INT64_C(4294944443);
        s[0] = s[1]; s[1] = s[2]; s[2] = (uint32_t)p;
        s[3] = s[4]; s[4] = s[5]; s[5] = (uint32_t)q;
        int64_t difference = p-q;
        if (difference <= 0) difference += INT64_C(4294967087);
        *value = (double)difference/4294967088.0;
        ++rng->draws[stream]; return 0;
    }
    if (rng->algorithm != 0 ||
        rng->state[stream] == 0 || rng->state[stream] >= UINT32_C(2147483647) ||
        rng->draws[stream] >= PMCSN_STREAM_SPACING - 1) return -1;
    rng->state[stream] = (uint32_t)((UINT64_C(48271) * rng->state[stream]) % UINT64_C(2147483647));
    ++rng->draws[stream];
    *value = rng->state[stream] / 2147483647.0;
    return 0;
}
