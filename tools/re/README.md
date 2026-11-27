# tools/re: read-only reverse-engineering helpers

Our own code (BSD-3-Clause). It produced the evidence in `docs/LLMs/re/`. Every tool is read-only: it never writes to the system, the ESP or the shared cache. Run Python with `-I`, and keep any extracted Apple images in a scratch directory outside the repo. Apple binaries and decompiled output are never committed.

| Tool | What it does |
|---|---|
| `dscx.c` | Extracts every image of a dyld shared cache with Apple's `/usr/lib/dsc_extractor.bundle`. Build: `clang -O2 -o dscx dscx.c`. Usage: `dscx <cache> <outdir>`. |
| `dsc_cs_check.py` | Checks every page of a shared-cache file against its CodeDirectory slots and prints the mismatching pages with their VM addresses. |
| `dsc_va2img.py` | Maps a shared-cache VM address to the image whose `__TEXT` contains it. |
| `dsc_str.py` | Reads C strings, CFStrings, selector refs and class refs at shared-cache VM addresses, across the main cache and its subcaches. |
| `abort_stubs.py` | Lists the ObjC methods of a class whose body is `push rbp; mov rbp,rsp; call <abort>`. Usage: `abort_stubs.py <image> <class> <abort-stub-va>`. |
| `csprobe.c` | Prints the kernel's dynamic code-signing state per pid (csops status flags, validation category, team ID, identity). Build: `clang -O2 -o csprobe csprobe.c`. Usage: `csprobe <pid>…`. |
| `ips_summary.py` | Groups `.ips` crash reports by crashed-thread signature, with sanitized paths. |
| `lv_timeline.py` | Aggregates AMFI `Library Validation …` lines from `/usr/bin/log show` on stdin. In zsh, `log` is a builtin, so call `/usr/bin/log`. |

## Extracting the 25G241 shared cache

1. Run `dscx /System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_x86_64h <scratch>/dsc`.
2. On the legacy stack the extractor refuses the cache, because one page fails its hash. `dsc_cs_check.py` on the main file names the page: on 25G241, page 67726, in `AppleSystemInfo` text. A user-space patcher modifies that page in memory. To work around it:
   1. Copy the main cache file into a scratch directory.
   2. In the copy, rewrite that one page's hash slot in each CodeDirectory to the page's current SHA-256.
   3. Symlink the `.01`–`.06` subcaches next to the copy.
   4. Extract from the copy.

   Every other page still verifies.
3. Run `nm -m` and `dwarfdump --uuid` on the extracted images. They give the unslid addresses and LC_UUIDs cited in the findings.
