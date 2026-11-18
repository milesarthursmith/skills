"""Apply the two clustering passes to the feedback log and write a cluster summary.

Usage: python3 -I scripts/cluster_apply.py feedback_log.jsonl clusters/ out_prefix
Reads clusters/chunk_XX.json (pass 1) and clusters/final.json (pass 2).
Writes:
  out_prefix.jsonl / .csv   the feedback log with a "cluster" column
  out_prefix_clusters.csv   one row per final cluster: counts, dates, months seen, sessions, example quotes
Rows that no pass-1 cluster listed get cluster "(unassigned)". The script prints how many.
"""
import csv, json, re, sys
from collections import defaultdict
from pathlib import Path

log, d, prefix = sys.argv[1], Path(sys.argv[2]), sys.argv[3]


def load_clusters(p):
    t = Path(p).read_text()
    m = re.search(r"\{.*\}", t, re.S)
    return json.loads(m.group(0))["clusters"]


final = load_clusters(d / "final.json")
member_to_final = {}
for c in final:
    for mem in c.get("members", []):
        member_to_final[mem] = c["name"]

row_cluster, dup = {}, 0
for j in sorted(d.glob("chunk_*.json")):
    for c in load_clusters(j):
        name = member_to_final.get(f"{j.stem}.{c['id']}", "(not merged)")
        for lid in c.get("log_ids", []):
            lid = int(re.sub(r"\D", "", str(lid)) or 0)
            if lid in row_cluster:
                dup += 1
            row_cluster[lid] = name

rows = [json.loads(l) for l in open(log)]
for r in rows:
    r["cluster"] = row_cluster.get(r["log_id"], "(unassigned)")

cols = list(rows[0].keys()) if rows else []
with open(prefix + ".jsonl", "w") as o:
    for r in rows:
        o.write(json.dumps(r, ensure_ascii=False) + "\n")
with open(prefix + ".csv", "w", newline="") as o:
    w = csv.DictWriter(o, fieldnames=cols); w.writeheader()
    for r in rows:
        w.writerow({c: (r[c][:49000] if isinstance(r[c], str) else r[c]) for c in cols})

by = defaultdict(list)
for r in rows:
    by[r["cluster"]].append(r)
info = {c["name"]: c for c in final}
summary = []
for name, rs in sorted(by.items(), key=lambda kv: -len(kv[1])):
    dates = sorted(r["date"] for r in rs if r["date"])
    months = sorted({x[:7] for x in dates})
    quotes = [r["quote"] for r in rs if r.get("quote_verified")][:3]
    summary.append({
        "cluster": name, "definition": info.get(name, {}).get("definition", ""),
        "rule": info.get(name, {}).get("rule", ""), "rows": len(rs),
        "negative": sum(r["sentiment"] == "negative" for r in rs), "positive": sum(r["sentiment"] == "positive" for r in rs),
        "sessions": len({r["session"] for r in rs if r["session"]}), "first": dates[0] if dates else "",
        "last": dates[-1] if dates else "", "months_seen": len(months),
        "projects": ", ".join(sorted({r["project"] for r in rs if r["project"]})[:8]),
        "example_quotes": " || ".join(quotes), "log_ids": ", ".join(str(r["log_id"]) for r in rs[:10]),
    })
with open(prefix + "_clusters.csv", "w", newline="") as o:
    w = csv.DictWriter(o, fieldnames=list(summary[0].keys())); w.writeheader(); w.writerows(summary)

un = len(by.get("(unassigned)", [])); nm = len(by.get("(not merged)", []))
print(f"{len(final)} final clusters over {len(rows)} rows; {un} unassigned, {nm} in pass-1 clusters not merged, {dup} listed twice")
for s in summary[:15]:
    print(f"{s['rows']:5}  {s['cluster']}  ({s['first']} to {s['last']}, {s['months_seen']} months)")
