#include "rome_bus_pmcsn/audit.h"
#include <string.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr, "Failed at line %d: %s\n", __LINE__, #x); return 1; } } while (0)
int main(void) {
    uint64_t t;
    CHECK(!gtfs_time("25:01:02", &t) && t == 90062);
    CHECK(gtfs_time("24:60:00", &t)); CHECK(gtfs_time("1:2", &t));
    CHECK(gtfs_time("999999999999999999999:00:00", &t));
    FILE *f = tmpfile(); CHECK(f);
    fputs("id,name,empty\r\n1,\"A, B\",\r\n2,\"a\"\"b\",x\n", f); rewind(f);
    char buffer[128], *fields[4];
    CHECK(csv_row(f, buffer, sizeof(buffer), fields, 4) == 3);
    CHECK(csv_row(f, buffer, sizeof(buffer), fields, 4) == 3 && !strcmp(fields[1], "A, B") && !*fields[2]);
    CHECK(csv_row(f, buffer, sizeof(buffer), fields, 4) == 3 && !strcmp(fields[1], "a\"b"));
    CHECK(csv_row(f, buffer, sizeof(buffer), fields, 4) == 0); fclose(f);
    f = tmpfile(); CHECK(f); fputs("\"broken", f); rewind(f);
    CHECK(csv_row(f, buffer, sizeof(buffer), fields, 4) == -1); fclose(f);
    f = tmpfile(); CHECK(f); fputs("\"closed\"suffix,x", f); rewind(f);
    CHECK(csv_row(f, buffer, sizeof(buffer), fields, 4) == -1); fclose(f);
    f = tmpfile(); CHECK(f); fputs("a,b,c", f); rewind(f);
    CHECK(csv_row(f, buffer, sizeof(buffer), fields, 2) == -1); fclose(f);
    unsigned char valid[] = {10, 7, 10, 3, '2', '.', '0', 24, 1};
    f = tmpfile(); CHECK(f); CHECK(!audit_feed(valid, sizeof(valid), f));
    CHECK(audit_feed(valid, sizeof(valid)-1, f));
    unsigned char overflow[] = {128,128,128,128,128,128,128,128,128,2};
    CHECK(audit_feed(overflow, sizeof(overflow), f));
    CHECK(audit_feed(NULL, 0, f));
    unsigned char missing[] = {10, 0}; CHECK(audit_feed(missing, sizeof(missing), f));
    unsigned char empty_feed[] = {10, 5, 10, 3, '2', '.', '0'};
    CHECK(!audit_feed(empty_feed, sizeof(empty_feed), f));
    unsigned char missing_id[] = {10,5,10,3,'2','.','0',18,0};
    CHECK(audit_feed(missing_id, sizeof(missing_id), f));
    unsigned char trip_feed[] = {10,5,10,3,'2','.','0',18,12,10,1,'e',34,7,10,5,10,3,'1','2','3'};
    CHECK(!audit_feed(trip_feed, sizeof(trip_feed), f));
    FILE *ids = tmpfile(); CHECK(ids);
    CHECK(!feed_trip_ids(trip_feed, sizeof(trip_feed), ids)); rewind(ids);
    char line[64]; CHECK(fgets(line, sizeof(line), ids) && !strcmp(line, "trip_id\n"));
    CHECK(fgets(line, sizeof(line), ids) && !strcmp(line, "\"123\"\n")); fclose(ids);
    fclose(f); return 0;
}
