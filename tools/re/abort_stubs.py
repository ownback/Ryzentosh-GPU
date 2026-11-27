# SPDX-License-Identifier: BSD-3-Clause
# abort_stubs.py: list ObjC methods of a class whose body is "push rbp; mov rbp,rsp; call <abort stub>" (read-only).
import struct, subprocess, sys
path, cls, abort_va = sys.argv[1], sys.argv[2], int(sys.argv[3], 16)
d = open(path, 'rb').read()
ncmds = struct.unpack_from('<I', d, 16)[0]; off = 32; segs = []
for _ in range(ncmds):
    cmd, sz = struct.unpack_from('<II', d, off)
    if cmd == 0x19:
        vmaddr, vmsize, fileoff, filesize = struct.unpack_from('<QQQQ', d, off + 24); segs.append((vmaddr, vmsize, fileoff))
    off += sz
def fo(va):
    for a, s, f in segs:
        if a <= va < a + s: return f + va - a
nm = subprocess.run(['nm', path], capture_output=True, text=True).stdout.splitlines()
stubs, total = [], 0
for line in nm:
    parts = line.split(' ', 2)
    if len(parts) < 3 or not parts[2].startswith(f'-[{cls} ') and not parts[2].startswith(f'+[{cls} '): continue
    total += 1; va = int(parts[0], 16); o = fo(va)
    if o is None: continue
    b = d[o:o + 9]
    if b[:5] == b'\x55\x48\x89\xe5\xe8':
        tgt = va + 9 + struct.unpack_from('<i', b, 5)[0]
        if tgt == abort_va: stubs.append(parts[2])
print(f"{cls}: {total} methods, {len(stubs)} abort() stubs")
for s in sorted(stubs): print("  ", s)
