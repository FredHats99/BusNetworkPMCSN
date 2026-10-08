#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <winhttp.h>
#endif
/* HTTPS only, native Windows TLS; no shell invocation. New files only. */
int download_feed(const char *name, const char *path) {
#ifdef _WIN32
    const char *files[] = {"static", "vehicles", "updates", "alerts"};
    const wchar_t *urls[] = {L"/sites/default/files/rome_static_gtfs.zip", L"/sites/default/files/rome_rtgtfs_vehicle_positions_feed.pb", L"/sites/default/files/rome_rtgtfs_trip_updates_feed.pb", L"/sites/default/files/rome_rtgtfs_service_alerts_feed.pb"};
    unsigned index;
    for (index = 0; index < 4 && strcmp(name, files[index]); ++index) {}
    if (index == 4) return 1;
    HANDLE file = CreateFileA(path, GENERIC_WRITE, 0, NULL, CREATE_NEW, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) { fprintf(stderr, "Cannot create new file: %s (error %lu)\n", path, GetLastError()); return 1; }
    HINTERNET session = WinHttpOpen(L"RomeBusPMCSN/0.1 (academic feed audit)", WINHTTP_ACCESS_TYPE_AUTOMATIC_PROXY, NULL, NULL, 0);
    HINTERNET connection = NULL, request = NULL;
    int result = 1;
    if (!session) goto cleanup;
    WinHttpSetTimeouts(session, 10000, 10000, 10000, 30000);
    connection = WinHttpConnect(session, L"romamobilita.it", INTERNET_DEFAULT_HTTPS_PORT, 0);
    if (!connection) goto cleanup;
    request = WinHttpOpenRequest(connection, L"GET", urls[index], NULL, NULL, NULL, WINHTTP_FLAG_SECURE);
    if (!request || !WinHttpSendRequest(request, NULL, 0, NULL, 0, 0, 0) || !WinHttpReceiveResponse(request, NULL)) goto cleanup;
    DWORD status = 0, length = sizeof(status);
    if (!WinHttpQueryHeaders(request, WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER, NULL, &status, &length, NULL) || status != 200) { fprintf(stderr, "HTTP status: %lu\n", status); goto cleanup; }
    unsigned char buffer[65536]; DWORD read, written; size_t total = 0;
    for (;;) {
        if (!WinHttpReadData(request, buffer, sizeof(buffer), &read)) goto cleanup;
        if (!read) break;
        if (total > 512u * 1024u * 1024u - read) goto cleanup;
        if (!WriteFile(file, buffer, read, &written, NULL) || written != read) goto cleanup;
        total += read;
    }
    if (!total || !FlushFileBuffers(file)) goto cleanup;
    printf("downloaded=%zu bytes path=%s\n", total, path); result = 0;
cleanup:
    if (result) fprintf(stderr, "Download failed (Windows error %lu)\n", GetLastError());
    if (request) WinHttpCloseHandle(request);
    if (connection) WinHttpCloseHandle(connection);
    if (session) WinHttpCloseHandle(session);
    CloseHandle(file);
    if (result) DeleteFileA(path);
    return result;
#else
    (void)name; (void)path;
    fprintf(stderr, "HTTP backend currently implemented for Windows only.\n"); return 1;
#endif
}
