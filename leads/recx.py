"""Merge results into a given JSON file.
Usage: python3 recx.py <outfile.json> '<json list>'
Each item: {"n": 12, "email": "...", "website": "...", "all": "...", "source": "...", "status": "..."}
"""
import json, sys, os
P = sys.argv[1]
res = json.load(open(P)) if os.path.exists(P) else {}
items = json.loads(sys.argv[2])
for it in items:
    k = str(it['n'])
    cur = res.get(k, {})
    cur.update({kk: vv for kk, vv in it.items() if kk != 'n'})
    res[k] = cur
json.dump(res, open(P, 'w'), ensure_ascii=False, indent=0)
print(f'recorded {len(items)}; total in file {len(res)}')
