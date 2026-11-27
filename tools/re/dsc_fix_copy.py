# SPDX-License-Identifier: BSD-3-Clause
# dsc_fix_copy.py: on a COPY of a dyld shared cache file, rewrite the CodeDirectory hash slots of pages whose
# current bytes no longer match (pages patched in memory are visible through the unified buffer cache), so that
# dsc_extractor accepts the copy. Prints every slot it rewrites. Refuses to touch the system's own cache.
import hashlib, os, struct, sys

def be32(b, o): return struct.unpack_from('>I', b, o)[0]

path = os.path.realpath(sys.argv[1])
if path.startswith(('/System/', '/private/var/db/dyld', '/usr/', '/Library/')) or not os.access(path, os.W_OK):
    sys.exit('refusing: pass a writable copy outside the system locations')
with open(path, 'r+b') as f:
    hdr = f.read(0x200)
    cs_off, cs_size = struct.unpack_from('<QQ', hdr, 0x28)
    f.seek(cs_off); cs = bytearray(f.read(cs_size))
    if be32(cs, 0) != 0xfade0cc0: sys.exit('no code-signature superblob')
    fixed = 0
    for i in range(be32(cs, 8)):
        typ, off = struct.unpack_from('>II', cs, 12 + 8 * i)
        if be32(cs, off) != 0xfade0c02: continue
        ver, hash_off, n_code, code_limit = be32(cs, off + 8), be32(cs, off + 16), be32(cs, off + 28), be32(cs, off + 32)
        hsz, htype, pglog = cs[off + 36], cs[off + 37], cs[off + 39]
        if ver >= 0x20300:
            cl64 = struct.unpack_from('>Q', cs, off + 56)[0]
            if cl64: code_limit = cl64
        pg, algo = 1 << pglog, {1: 'sha1', 2: 'sha256', 3: 'sha256', 4: 'sha384'}[htype]
        f.seek(0)
        for p in range(n_code):
            h = hashlib.new(algo, f.read(min(pg, code_limit - p * pg))).digest()[:hsz]
            so = off + hash_off + p * hsz
            if bytes(cs[so:so + hsz]) != h:
                cs[so:so + hsz] = h; fixed += 1
                print(f'CodeDirectory slot 0x{typ:x} ({algo}): page {p} (file offset 0x{p * pg:x}) rewritten')
    f.seek(cs_off); f.write(cs)
print('slots rewritten:', fixed)
