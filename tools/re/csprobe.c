// SPDX-License-Identifier: BSD-3-Clause
// csprobe: print the kernel's dynamic code-signing status of running processes (read-only csops).
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>
#include <arpa/inet.h>
#include <libproc.h>
#include <sys/types.h>
extern int csops(pid_t pid, unsigned int ops, void *useraddr, size_t usersize);
static const struct { uint32_t bit; const char *name; } F[] = {
 {0x1,"VALID"},{0x2,"ADHOC"},{0x4,"GET_TASK_ALLOW"},{0x8,"INSTALLER"},{0x10,"FORCED_LV"},
 {0x20,"INVALID_ALLOWED"},{0x100,"HARD"},{0x200,"KILL"},{0x400,"CHECK_EXPIRATION"},{0x800,"RESTRICT"},
 {0x1000,"ENFORCEMENT"},{0x2000,"REQUIRE_LV"},{0x4000,"ENTITLEMENTS_VALIDATED"},{0x8000,"NVRAM_UNRESTRICTED"},
 {0x10000,"RUNTIME"},{0x20000,"LINKER_SIGNED"},{0x100000,"EXEC_SET_HARD"},{0x200000,"EXEC_SET_KILL"},
 {0x400000,"EXEC_SET_ENFORCEMENT"},{0x800000,"EXEC_INHERIT_SIP"},{0x1000000,"KILLED"},
 {0x2000000,"NO_UNTRUSTED_HELPERS"},{0x4000000,"PLATFORM_BINARY"},{0x8000000,"PLATFORM_PATH"},
 {0x10000000,"DEBUGGED"},{0x20000000,"SIGNED"},{0x40000000,"DEV_CODE"},{0x80000000,"DATAVAULT_CONTROLLER"}};
static const char *CAT[] = {"invalid","platform","testflight","development","app-store","enterprise",
 "developer-id","local-signing","rosetta","oop-jit","none"};
static void blobstr(pid_t pid, unsigned op, char *out, size_t n) {
  unsigned char buf[1024]; memset(buf,0,sizeof buf); out[0]=0;
  if (csops(pid, op, buf, sizeof buf) != 0) { snprintf(out,n,"(err %d)",errno); return; }
  uint32_t len = ntohl(*(uint32_t*)(buf+4));
  if (len > 8 && len < sizeof buf) snprintf(out,n,"%.*s",(int)(len-8),(char*)buf+8); else snprintf(out,n,"-");
}
int main(int argc, char **argv) {
  for (int i = 1; i < argc; i++) {
    pid_t pid = atoi(argv[i]); uint32_t fl = 0; char path[PROC_PIDPATHINFO_MAXSIZE] = "";
    proc_pidpath(pid, path, sizeof path);
    const char *base = strrchr(path,'/'); base = base ? base+1 : path;
    if (csops(pid, 0 /*CS_OPS_STATUS*/, &fl, sizeof fl) != 0) { printf("%d %s status-err %d\n", pid, base, errno); continue; }
    unsigned cat = 0; int cr = csops(pid, 17 /*CS_OPS_VALIDATION_CATEGORY*/, &cat, sizeof cat);
    char team[256], ident[512]; blobstr(pid, 14, team, sizeof team); blobstr(pid, 11, ident, sizeof ident);
    printf("%d\t%s\tflags=0x%08x\tcat=%s\tteam=%s\tid=%s\t[", pid, base, fl,
           cr==0 && cat<=10 ? CAT[cat] : "?", team, ident);
    for (size_t k = 0; k < sizeof F/sizeof F[0]; k++) if (fl & F[k].bit) printf(" %s", F[k].name);
    printf(" ]\n");
  }
  return 0;
}
