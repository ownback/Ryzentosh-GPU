# SPDX-License-Identifier: BSD-3-Clause
# ips_summary.py: summarize crashed-thread frames of .ips crash reports (sanitized: no UUIDs, users, hosts).
import json, sys, collections, os, re
def load(p):
    with open(p, 'r', errors='replace') as f:
        head = f.readline(); body = f.read()
    try: return json.loads(head), json.loads(body)
    except Exception as e: return None, None
def frames(b, tidx, n=14):
    imgs = b.get('usedImages', [])
    th = b['threads'][tidx]
    out = []
    for fr in th.get('frames', [])[:n]:
        ii = fr.get('imageIndex'); img = imgs[ii] if ii is not None and ii < len(imgs) else {}
        name = img.get('name') or os.path.basename(img.get('path','?') or '?')
        sym = fr.get('symbol', '?'); off = fr.get('symbolLocation', fr.get('imageOffset'))
        out.append(f"{name}: {sym} + {off}")
    return out
sigs = collections.Counter(); example = {}
for p in sys.argv[1:]:
    h, b = load(p)
    if not b: continue
    exc = b.get('exception', {}); term = b.get('termination', {})
    ct = next((i for i, t in enumerate(b.get('threads', [])) if t.get('triggered')), 0)
    fr = frames(b, ct)
    key = (exc.get('type'), exc.get('signal'), exc.get('subtype','')[:60], term.get('indicator',''), tuple(fr[:6]))
    sigs[key] += 1; example.setdefault(key, (p, fr, b))
for key, c in sigs.most_common():
    p, fr, b = example[key]
    print(f"=== {c}x  exc={key[0]} sig={key[1]} sub={key[2]} term={key[3]}")
    print("   os:", b.get('osVersion', {}).get('train'), b.get('osVersion', {}).get('build'), " proc:", b.get('procName'), " path:", re.sub(r'/Users/[^/]+','~', b.get('procPath','')))
    print("   example:", os.path.basename(p), " crashed thread queue:", b['threads'][next((i for i,t in enumerate(b['threads']) if t.get('triggered')),0)].get('queue'))
    for f in fr: print("     ", f)
