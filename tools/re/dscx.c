// SPDX-License-Identifier: BSD-3-Clause
// dscx: extract all dylibs of a dyld shared cache with Apple's /usr/lib/dsc_extractor.bundle.
#include <stdio.h>
#include <dlfcn.h>
typedef int (*extract_fn)(const char *cache, const char *root, void (^progress)(unsigned, unsigned));
int main(int argc, char **argv) {
  if (argc != 3) { fprintf(stderr, "usage: dscx <cache> <outdir>\n"); return 64; }
  void *h = dlopen("/usr/lib/dsc_extractor.bundle", RTLD_NOW);
  if (!h) { fprintf(stderr, "dlopen: %s\n", dlerror()); return 1; }
  extract_fn f = (extract_fn)dlsym(h, "dyld_shared_cache_extract_dylibs_progress");
  if (!f) { fprintf(stderr, "dlsym failed\n"); return 1; }
  int r = f(argv[1], argv[2], ^(unsigned c, unsigned t) { if (c % 200 == 0) fprintf(stderr, "%u/%u\n", c, t); });
  fprintf(stderr, "result %d\n", r); return r;
}
