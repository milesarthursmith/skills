"""Combine learnings logs from several machines into one, renumbering log_id.

Usage: python3 -I scripts/combine_logs.py data/learnings_log_all.jsonl work=path/to/learnings_log.jsonl home=path/to/learnings_log.jsonl
Adds a "machine" field. Rows are sorted by date.
"""
import json, sys

out, pairs = sys.argv[1], [x.split("=", 1) for x in sys.argv[2:]]
rows = []
for machine, path in pairs:
    for l in open(path):
        r = json.loads(l); r["machine"] = machine; r["ref"] = f"{machine}:{r['ref']}"; rows.append(r)
rows.sort(key=lambda r: (r.get("date") or "9999", r["ref"]))
with open(out, "w") as o:
    for i, r in enumerate(rows, 1):
        r["log_id"] = i
        o.write(json.dumps(r, ensure_ascii=False) + "\n")
print(len(rows), "rows from", ", ".join(m for m, _ in pairs))
