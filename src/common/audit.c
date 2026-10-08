#include "rome_bus_pmcsn/audit.h"
#include <inttypes.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>

static int varint(PbReader *r, uint64_t *v) {
    *v = 0;
    for (unsigned i = 0; i < 10; ++i) {
        if (r->offset == r->size) return -1;
        unsigned char b = r->data[r->offset++];
        if (i == 9 && b > 1) return -1;
        *v |= (uint64_t)(b & 127) << (7 * i);
        if (!(b & 128)) return 0;
    }
    return -1;
}
int pb_next(PbReader *r, PbField *f) {
    uint64_t tag, length;
    memset(f, 0, sizeof(*f));
    if (r->offset == r->size) return 0;
    if (r->offset > r->size || varint(r, &tag) || !(tag >> 3) || (tag >> 3) > 536870911) return -1;
    f->number = (unsigned)(tag >> 3); f->wire = (unsigned)(tag & 7);
    if (f->wire == 0) return varint(r, &f->value) ? -1 : 1;
    if (f->wire == 2) { if (varint(r, &length)) return -1; }
    else if (f->wire == 1) length = 8;
    else if (f->wire == 5) length = 4;
    else return -1; /* deprecated groups unsupported */
    if (length > r->size - r->offset) return -1;
    f->data = r->data + r->offset; f->size = (size_t)length; r->offset += f->size;
    return 1;
}
static int fields_count(const unsigned char *data, size_t size, size_t counts[32]) {
    PbReader r = {data, size, 0}; PbField f; int rc;
    memset(counts, 0, 32 * sizeof(*counts));
    while ((rc = pb_next(&r, &f)) == 1) if (f.number < 32) counts[f.number]++;
    return rc;
}
int feed_trip_ids(const unsigned char *data, size_t size, FILE *out) {
    PbReader r = {data, size, 0}; PbField f; int rc;
    fputs("trip_id\n", out);
    while ((rc = pb_next(&r, &f)) == 1) {
        if (f.number != 2) continue;
        if (f.wire != 2) return -1;
        PbReader e = {f.data, f.size, 0}; PbField ef; int er;
        while ((er = pb_next(&e, &ef)) == 1) {
            if (ef.number != 3 && ef.number != 4) continue;
            if (ef.wire != 2) return -1;
            PbReader v = {ef.data, ef.size, 0}; PbField vf; int vr;
            while ((vr = pb_next(&v, &vf)) == 1) {
                if (vf.number != 1) continue;
                if (vf.wire != 2) return -1;
                PbReader t = {vf.data, vf.size, 0}; PbField tf; int tr;
                while ((tr = pb_next(&t, &tf)) == 1) {
                    if (tf.number != 1) continue;
                    if (tf.wire != 2) return -1;
                    fputc('"', out);
                    for (size_t i = 0; i < tf.size; ++i) {
                        if (tf.data[i] < 32) return -1;
                        if (tf.data[i] == '"') fputc('"', out);
                        fputc(tf.data[i], out);
                    }
                    fputs("\"\n", out);
                }
                if (tr < 0) return -1;
            }
            if (vr < 0) return -1;
        }
        if (er < 0) return -1;
    }
    return rc < 0 || ferror(out) ? -1 : 0;
}
int audit_feed(const unsigned char *data, size_t size, FILE *out) {
    PbReader r = {data, size, 0}; PbField f; int rc, header = 0;
    size_t entities = 0, vp = 0, tu = 0, alerts = 0, trip = 0, vehicle = 0;
    size_t timestamp = 0, sequence = 0, occupancy = 0, percentage = 0;
    size_t tu_trip = 0, tu_timestamp = 0, tu_stops = 0, tu_sequence = 0, tu_stop_id = 0;
    size_t event_delay = 0, event_time = 0, event_uncertainty = 0;
    uint64_t feed_timestamp = 0;
    while ((rc = pb_next(&r, &f)) == 1) {
        if (f.number == 1) {
            if (f.wire != 2 || header++) return -1;
            PbReader h = {f.data, f.size, 0}; PbField hf; int hr, version = 0;
            while ((hr = pb_next(&h, &hf)) == 1) {
                if (hf.number == 1 && hf.wire == 2 && hf.size) version = 1;
                if (hf.number == 3 && hf.wire == 0) feed_timestamp = hf.value;
            }
            if (hr < 0 || !version) return -1;
        } else if (f.number == 2) {
            if (f.wire != 2) return -1;
            entities++;
            PbReader e = {f.data, f.size, 0}; PbField ef; int er, id = 0;
            while ((er = pb_next(&e, &ef)) == 1) {
                if (ef.number == 1 && ef.wire == 2 && ef.size) id = 1;
                if (ef.number >= 3 && ef.number <= 5) {
                    size_t counts[32];
                    if (ef.wire != 2 || fields_count(ef.data, ef.size, counts)) return -1;
                    if (ef.number == 4) { vp++; trip += counts[1] != 0; vehicle += counts[8] != 0; timestamp += counts[5] != 0; sequence += counts[3] != 0; occupancy += counts[9] != 0; percentage += counts[10] != 0; }
                    if (ef.number == 3) {
                        tu++; tu_trip += counts[1] != 0; tu_timestamp += counts[4] != 0;
                        PbReader u = {ef.data, ef.size, 0}; PbField uf; int ur;
                        while ((ur = pb_next(&u, &uf)) == 1) if (uf.number == 2) {
                            size_t sc[32];
                            if (uf.wire != 2 || fields_count(uf.data, uf.size, sc)) return -1;
                            tu_stops++; tu_sequence += sc[1] != 0; tu_stop_id += sc[4] != 0;
                            PbReader s = {uf.data, uf.size, 0}; PbField sf; int sr;
                            while ((sr = pb_next(&s, &sf)) == 1) if (sf.number == 2 || sf.number == 3) {
                                size_t ec[32];
                                if (sf.wire != 2 || fields_count(sf.data, sf.size, ec)) return -1;
                                event_delay += ec[1] != 0; event_time += ec[2] != 0; event_uncertainty += ec[3] != 0;
                            }
                            if (sr < 0) return -1;
                        }
                        if (ur < 0) return -1;
                    }
                    if (ef.number == 5) alerts++;
                }
            }
            if (er < 0 || !id) return -1;
        }
    }
    if (rc < 0 || !header) return -1;
    fprintf(out, "feed_timestamp=%" PRIu64 "\nentities=%zu\nvehicle_positions=%zu\ntrip_updates=%zu\nalerts=%zu\nvp_trip_descriptor_present=%zu\nvp_vehicle_descriptor_present=%zu\nvp_timestamp_present=%zu\nvp_stop_sequence_present=%zu\nvp_occupancy_status_present=%zu\nvp_occupancy_percentage_present=%zu\n", feed_timestamp, entities, vp, tu, alerts, trip, vehicle, timestamp, sequence, occupancy, percentage);
    fprintf(out, "tu_trip_descriptor_present=%zu\ntu_timestamp_present=%zu\ntu_stop_updates=%zu\ntu_stop_sequence_present=%zu\ntu_stop_id_present=%zu\ntu_event_delay_present=%zu\ntu_event_time_present=%zu\ntu_event_uncertainty_present=%zu\n", tu_trip, tu_timestamp, tu_stops, tu_sequence, tu_stop_id, event_delay, event_time, event_uncertainty);
    return ferror(out) ? -1 : 0;
}
int csv_row(FILE *in, char *buffer, size_t capacity, char **fields, size_t max_fields) {
    size_t used = 0, count = 1; int quoted = 0, closed = 0, c, any = 0;
    if (!capacity || !max_fields) return -1;
    fields[0] = buffer;
    while ((c = fgetc(in)) != EOF) {
        any = 1;
        if (closed && c != ',' && c != '\r' && c != '\n') return -1;
        if (c == '"') {
            if (quoted) { int next = fgetc(in); if (next == '"') c = '"'; else { quoted = 0; closed = 1; if (next != EOF) ungetc(next, in); continue; } }
            else { if (buffer + used != fields[count - 1]) return -1; quoted = 1; continue; }
        } else if (!quoted && (c == '\n' || c == '\r')) {
            if (c == '\r') { int next = fgetc(in); if (next != '\n' && next != EOF) ungetc(next, in); }
            break;
        } else if (!quoted && c == ',') {
            if (used + 1 >= capacity || count == max_fields) return -1;
            buffer[used++] = 0; fields[count++] = buffer + used; closed = 0; continue;
        }
        if (used + 1 >= capacity) return -1;
        buffer[used++] = (char)c;
    }
    if (ferror(in) || quoted) return -1;
    if (!any) return 0;
    buffer[used] = 0; return (int)count;
}
int gtfs_time(const char *text, uint64_t *seconds) {
    uint64_t parts[3] = {0}; const char *p = text;
    for (unsigned i = 0; i < 3; ++i) {
        if (*p < '0' || *p > '9') return -1;
        while (*p >= '0' && *p <= '9') { unsigned digit = (unsigned)(*p++ - '0'); if (parts[i] > (UINT64_MAX - digit) / 10) return -1; parts[i] = parts[i] * 10 + digit; }
        if (i < 2 && *p++ != ':') return -1;
    }
    if (*p || parts[1] > 59 || parts[2] > 59 || parts[0] > (UINT64_MAX - 3599) / 3600) return -1;
    *seconds = parts[0] * 3600 + parts[1] * 60 + parts[2]; return 0;
}
