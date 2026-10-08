#ifndef PMCSN_AUDIT_H
#define PMCSN_AUDIT_H
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
/* Views borrow input memory; the caller retains ownership. */
typedef struct { const unsigned char *data; size_t size, offset; } PbReader;
typedef struct { unsigned number, wire; uint64_t value; const unsigned char *data; size_t size; } PbField;
int pb_next(PbReader *r, PbField *f); /* 1 field, 0 end, -1 invalid */
int audit_feed(const unsigned char *data, size_t size, FILE *out);
int feed_trip_ids(const unsigned char *data, size_t size, FILE *out);
int csv_row(FILE *in, char *buffer, size_t capacity, char **fields, size_t max_fields);
int gtfs_time(const char *text, uint64_t *seconds);
#endif
