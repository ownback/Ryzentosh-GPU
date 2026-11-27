# SPDX-License-Identifier: BSD-3-Clause
# lv_timeline.py: aggregate AMFI "Library Validation ..." unified-log lines (sanitized output).
import sys, re, collections
rows = collections.OrderedDict()
pat = re.compile(r"^(\S+ \S+).*?(Library Validation [a-z ()]+?)[:]? (?:Rejecting |overridden for |Library )?'([^']+)'.*?process '([^'(]+)\((\d+)\)'.*?(?:reason|failure): (.*)$")
for l in sys.stdin:
    m = pat.search(l.strip())
    if not m:
        print("UNPARSED", l.strip()[:220]); continue
    t, kind, lib, proc, pid, reason = m.groups()
    k = (kind, lib.split('/')[-1], proc, reason[:72])
    r = rows.setdefault(k, [t[11:19], t[11:19], 0, set()])
    r[1] = t[11:19]; r[2] += 1; r[3].add(pid)
for (kind, lib, proc, reason), (t0, t1, n, pids) in rows.items():
    p = ",".join(sorted(pids))[:40]
    print(f"{t0}-{t1} x{n:<3} {kind:30} {lib:28} {proc}({p}) :: {reason}")
