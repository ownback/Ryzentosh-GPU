# SPDX-License-Identifier: BSD-3-Clause
# dsc_va2img.py: map a VM address in the dyld shared cache to the image whose __TEXT contains it.
import struct, sys
path, va = sys.argv[1], int(sys.argv[2], 16)
f = open(path, 'rb'); hdr = f.read(0x200)
tOff, tCnt = struct.unpack_from('<QQ', hdr, 0x88)
f.seek(tOff); rows = [struct.unpack('<16sQII', f.read(32)) for _ in range(tCnt)]
def pathat(o):
    f.seek(o); return f.read(400).split(b'\0')[0].decode()
for uuid, la, tsz, po in rows:
    if la <= va < la + tsz:
        print(f"image={pathat(po)} text=[0x{la:x},0x{la+tsz:x}) uuid={uuid.hex()} va_off=0x{va-la:x}")
print("images in table:", tCnt)
