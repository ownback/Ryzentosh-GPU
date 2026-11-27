# SPDX-License-Identifier: BSD-3-Clause
# dsc_cs_check.py: verify every page of a dyld shared cache file against its embedded CodeDirectories (read-only).
import struct, sys, hashlib
def be32(b, o): return struct.unpack_from('>I', b, o)[0]
def check(path):
    f = open(path, 'rb'); hdr = f.read(0x200)
    magic = hdr[:16].rstrip(b'\0').decode()
    mapOff, mapCnt = struct.unpack_from('<II', hdr, 16)
    csOff, csSize = struct.unpack_from('<QQ', hdr, 0x28)
    uuid = hdr[0x58:0x68].hex()
    f.seek(mapOff); maps = [struct.unpack('<QQQII', f.read(32)) for _ in range(mapCnt)]
    f.seek(csOff); cs = f.read(csSize)
    assert be32(cs, 0) == 0xfade0cc0, 'no superblob'
    count = be32(cs, 8); cds = []
    for i in range(count):
        typ, off = struct.unpack_from('>II', cs, 12 + 8*i)
        if be32(cs, off) == 0xfade0c02: cds.append((typ, off))
    print(f"{path.split('/')[-1]}: magic={magic!r} uuid={uuid} csOff=0x{csOff:x} CDs={len(cds)}")
    bad_all = None
    for typ, off in cds:
        ver = be32(cs, off+8); hashOff = be32(cs, off+16); nCode = be32(cs, off+28); codeLimit = be32(cs, off+32)
        hsz, htype, plat, pglog = cs[off+36], cs[off+37], cs[off+38], cs[off+39]
        if ver >= 0x20300:
            cl64 = struct.unpack_from('>Q', cs, off+56)[0]
            if cl64: codeLimit = cl64
        pg = 1 << pglog; algo = {1: 'sha1', 2: 'sha256', 3: 'sha256', 4: 'sha384'}[htype]
        bad = []; f.seek(0)
        for i in range(nCode):
            data = f.read(min(pg, codeLimit - i*pg))
            h = hashlib.new(algo, data).digest()[:hsz]
            if h != cs[off+hashOff+i*hsz: off+hashOff+(i+1)*hsz]: bad.append(i)
        print(f"   CD slot 0x{typ:x}: {algo} page={pg} nCode={nCode} codeLimit=0x{codeLimit:x} mismatched pages={len(bad)}")
        bad_all = bad if bad_all is None else bad_all
    for i in (bad_all or []):
        fo = i * pg
        m = [mp for mp in maps if mp[2] <= fo < mp[2] + mp[1]]
        va = (m[0][0] + fo - m[0][2]) if m else None
        print(f"      bad page {i}: fileoff=0x{fo:x} vm={'0x%x'%va if va else '?'} prot={m[0][4] if m else '?'}")
for p in sys.argv[1:]: check(p)
