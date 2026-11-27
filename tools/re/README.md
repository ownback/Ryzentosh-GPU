# tools/re: read-only reverse-engineering helpers

Our own code (BSD-3-Clause). It produced the evidence in `docs/LLMs/re/`. No tool writes to the system volume, the ESP or the live shared cache. `dsc_fix_copy.py` changes only the copy it is given. Run Python with `-I`, and keep any extracted Apple images in a scratch directory outside the repo. Apple binaries and decompiled output are never committed.

| Tool | What it does |
|---|---|
| `dscx.c` | Extracts every image of a dyld shared cache with Apple's `/usr/lib/dsc_extractor.bundle`. Build: `clang -O2 -o dscx dscx.c`. Usage: `dscx <cache> <outdir>`. |
| `dsc_cs_check.py` | Checks every page of a shared-cache file against its CodeDirectory slots and prints the mismatching pages with their VM addresses. |
| `dsc_fix_copy.py` | On a **copy** of a shared-cache file, rewrites the CodeDirectory hash slot of every page whose bytes no longer match, so that `dsc_extractor` accepts the copy. Prints each rewritten slot, then the total. Refuses paths under `/System`, `/usr`, `/Library` and `/private/var/db/dyld`. Usage: `dsc_fix_copy.py <copy>`. |
| `kext_superclass.py` | Prints the superclass of each libkern C++ class in a thin x86_64 kext, from its `X::superClass` pointer: an external relocation when the superclass is in another binary, the in-image metaclass address otherwise. Usage: `kext_superclass.py <kext binary> [Class…]`; thin first with `lipo -thin x86_64`. |
| `dsc_va2img.py` | Maps a shared-cache VM address to the image whose `__TEXT` contains it. |
| `dsc_str.py` | Reads C strings, CFStrings, selector refs and class refs at shared-cache VM addresses, across the main cache and its subcaches. |
| `abort_stubs.py` | Lists the ObjC methods of a class whose body is `push rbp; mov rbp,rsp; call <abort>`. Usage: `abort_stubs.py <image> <class> <abort-stub-va>`. |
| `csprobe.c` | Prints the kernel's dynamic code-signing state per pid (csops status flags, validation category, team ID, identity). Build: `clang -O2 -o csprobe csprobe.c`. Usage: `csprobe <pid>…`. |
| `ips_summary.py` | Groups `.ips` crash reports by crashed-thread signature, with sanitized paths. |
| `lv_timeline.py` | Aggregates AMFI `Library Validation …` lines from `/usr/bin/log show` on stdin. In zsh, `log` is a builtin, so call `/usr/bin/log`. |

## Extracting the 25G241 shared cache

1. Run `dscx /System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_x86_64h <scratch>/dsc`.
2. If the extractor refuses the cache because a page fails its hash, run `dsc_cs_check.py` on the main file to name the page. On the 2026-11-27 boot of the legacy stack it was page 67726, in `AppleSystemInfo` text, which a user-space patcher had modified in memory. After the next reboot no page mismatched. To work around a mismatch:
   1. Copy the main cache file into a scratch directory.
   2. Run `dsc_fix_copy.py` on the copy. It rewrites the bad page's hash slot in each CodeDirectory to the page's current hash.
   3. Symlink the `.01`–`.06` subcaches next to the copy.
   4. Extract from the copy.

   Every other page still verifies.
3. Run `nm -m` and `dwarfdump --uuid` on the extracted images. They give the unslid addresses and LC_UUIDs cited in the findings.
