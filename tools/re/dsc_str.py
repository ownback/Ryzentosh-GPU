# SPDX-License-Identifier: BSD-3-Clause
# dsc_str.py: read C strings / pointers at shared-cache VM addresses across the main cache and subcaches (read-only).
# usage: dsc_str.py sel <chained-or-va>...   |  cfstr <va>...  |  str <va>...
import struct, sys, glob
BASE = "/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_x86_64h"
maps = []
for p in [BASE] + sorted(glob.glob(BASE + ".0?")):
    f = open(p, 'rb'); h = f.read(0x200); mo, mc = struct.unpack_from('<II', h, 16); f.seek(mo)
    for _ in range(mc):
        a, s, fo, mx, ip = struct.unpack('<QQQII', f.read(32)); maps.append((a, s, fo, p))
def read(va, n):
    for a, s, fo, p in maps:
        if a <= va < a + s:
            f = open(p, 'rb'); f.seek(fo + va - a); return f.read(n)
    return None
def cstr(va):
    b = read(va, 300); return b.split(b'\0')[0].decode(errors='replace') if b else '<unmapped>'
def unchain(v):  # x86_64 cache: low 36 bits = offset from the cache base 0x7ff800000000
    return v if v >= 0x7ff800000000 else 0x7ff800000000 + (v & 0xFFFFFFFFF)
mode = sys.argv[1]
for x in sys.argv[2:]:
    v = int(x, 16)
    if mode == 'sel': print(x, '->', cstr(unchain(v)))
    elif mode == 'str': print(x, '->', cstr(v))
    elif mode == 'cfstr':
        b = read(v, 32); isa, flags, ptr, ln = struct.unpack('<QQQQ', b); print(x, '-> cfstr', repr(cstr(unchain(ptr))), 'len', ln)
if mode == 'selref':
    for x in sys.argv[2:]:
        v = struct.unpack('<Q', read(int(x, 16), 8))[0]; print(x, '-> selref', hex(v), '->', cstr(unchain(v)))
if mode == 'classref':  # classref -> class_t -> class_ro_t -> name
    for x in sys.argv[2:]:
        c = unchain(struct.unpack('<Q', read(int(x, 16), 8))[0])
        data = unchain(struct.unpack('<Q', read(c + 32, 8))[0]) & ~7
        name = unchain(struct.unpack('<Q', read(data + 24, 8))[0])
        print(x, '-> class', hex(c), 'name', cstr(name))
