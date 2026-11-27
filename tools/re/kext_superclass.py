# SPDX-License-Identifier: BSD-3-Clause
# kext_superclass.py: print the superclass of each libkern C++ class in a thin x86_64 kext (read-only).
# Each class X has a pointer X::superClass to its superclass's metaclass object (S::gMetaClass). When S lives in
# another kext or the kernel, an external relocation on that pointer names it. When S lives in the same kext, the
# pointer holds the metaclass address, which the symbol table names. Relocation addresses are taken relative to the
# first segment (KDK kexts start at vmaddr 0). A pointer that resolves neither way prints as "?".
# usage: python3 -I kext_superclass.py <thin x86_64 kext binary> [ClassName ...]   (thin with: lipo -thin x86_64)
import struct, subprocess, sys

d = open(sys.argv[1], 'rb').read()
if struct.unpack_from('<I', d, 0)[0] != 0xfeedfacf:
    sys.exit('not a thin 64-bit Mach-O')
ncmds, off = struct.unpack_from('<I', d, 16)[0], 32
segs, symoff, nsyms, stroff, extreloff, nextrel = [], 0, 0, 0, 0, 0
for _ in range(ncmds):
    cmd, size = struct.unpack_from('<II', d, off)
    if cmd == 0x19:    # LC_SEGMENT_64: vmaddr, vmsize, fileoff, filesize
        vmaddr, _, fileoff, filesize = struct.unpack_from('<QQQQ', d, off + 24)
        segs.append((vmaddr, fileoff, filesize))
    elif cmd == 0x2:   # LC_SYMTAB
        symoff, nsyms, stroff = struct.unpack_from('<III', d, off + 8)
    elif cmd == 0xb:   # LC_DYSYMTAB: extreloff and nextrel are its 15th and 16th fields
        extreloff, nextrel = struct.unpack_from('<II', d, off + 8 + 4 * 14)
    off += size

def name(i):
    return d[stroff + struct.unpack_from('<I', d, symoff + 16 * i)[0]:].split(b'\0')[0].decode()

def pointer_at(va):
    for vmaddr, fileoff, filesize in segs:
        if vmaddr <= va < vmaddr + filesize:
            return struct.unpack_from('<Q', d, fileoff + va - vmaddr)[0]

syms = []   # (name, value) of symbols defined in a section of this image, debug entries skipped
for i in range(nsyms):
    n_type, _, _, n_value = struct.unpack_from('<BBhQ', d, symoff + 16 * i + 4)
    if not n_type & 0xe0 and (n_type & 0x0e) == 0x0e:
        syms.append((name(i), n_value))
defined_at = {value: s for s, value in syms}
extern = {}
base = segs[0][0] if segs else 0
for i in range(nextrel):
    r_address, info = struct.unpack_from('<iI', d, extreloff + 8 * i)
    if (info >> 27) & 1:   # r_extern: the low 24 bits index the symbol table
        extern[base + r_address] = name(info & 0xffffff)

demangle = lambda s: subprocess.run(['c++filt', '-_', s], capture_output=True, text=True).stdout.strip()
want = set(sys.argv[2:])
for s, va in sorted(syms, key=lambda e: e[1]):
    if not s.endswith('10superClassE'):
        continue
    cls = demangle(s).removesuffix('::superClass')
    if want and cls not in want:
        continue
    sup = extern.get(va) or defined_at.get(pointer_at(va))
    print(f'{cls:40s} : {demangle(sup).removesuffix("::gMetaClass") if sup else "?"}')
