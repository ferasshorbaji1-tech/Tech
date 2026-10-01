"""Merge verification results into results.json.
Usage: python3 rec.py '<json list>'   where each item is
  {"n": 12, "email": "x@y.com", "website": "https://...", "source": "...", "status": "...", "all": "a@b.com; c@d.com"}
Fields other than n are optional; omitted fields keep previous values.
"""
import json, sys, os
P = os.path.join(os.path.dirname(__file__), 'results.json')
res = json.load(open(P)) if os.path.exists(P) else {}
items = json.loads(sys.argv[1])
for it in items:
    k = str(it['n'])
    cur = res.get(k, {})
    cur.update({kk: vv for kk, vv in it.items() if kk != 'n'})
    res[k] = cur
json.dump(res, open(P, 'w'), ensure_ascii=False, indent=0)
print(f'recorded {len(items)}; total {len(res)}')
