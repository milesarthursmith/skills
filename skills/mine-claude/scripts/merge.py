"""Merge Haiku outputs into one learnings log and check each quote against the full source text.

Usage: python3 -I scripts/merge.py data/messages.jsonl data/batches data/learnings_log
Writes OUT_PREFIX.jsonl and OUT_PREFIX.csv
"""
import csv, glob, html, json, re, sys
from collections import Counter

msgs, bdir, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
def norm(s): return re.sub(r"\s+", " ", html.unescape(s or "")).strip().lower()
ctx = {}
for l in open(msgs):
    r = json.loads(l); ctx[r["k"]] = r

rows, bad, none_batches = [], 0, 0
for f in sorted(glob.glob(f"{bdir}/out_b*.jsonl")):
    for line in open(f):
        line = line.strip()
        if not line or line == "NONE":
            continue
        try:
            x = json.loads(line)
            k = int(re.sub(r"\D", "", str(x.get("ref"))))
        except Exception:
            bad += 1; continue
        m = ctx.get(k)
        if not m:
            bad += 1; continue
        q = x.get("quote", "") or ""
        hay = {"me": m["text"], "note": m["text"], "claude_before": m["claude_before"], "claude_after": m["claude_after"]}
        nq = norm(q)
        found = next((name for name, t in hay.items() if nq and nq in norm(t)), "")
        rows.append({
            "date": (m.get("ts") or "")[:10], "source": m["source"], "title": m.get("title") or "",
            "project": x.get("project", ""), "type": x.get("type", ""), "category": x.get("category", ""),
            "summary": x.get("summary", ""), "lesson": x.get("lesson", ""), "quote": q,
            "quote_from": found or x.get("quote_from", ""), "quote_verified": bool(found),
            "my_message": m["text"], "claude_before": m["claude_before"], "claude_after": m["claude_after"],
            "session": m.get("session", ""), "ref": f"k={k}", "batch": f.rsplit("_", 1)[-1].split(".")[0],
        })

cols = ["log_id", "date", "source", "title", "project", "type", "category", "summary", "lesson", "quote", "quote_from",
        "quote_verified", "my_message", "claude_before", "claude_after", "session", "ref", "batch"]
rows.sort(key=lambda r: (r["date"] or "9999", r["ref"]))
for i, r in enumerate(rows):
    r["log_id"] = i + 1
with open(prefix + ".jsonl", "w") as o:
    for r in rows:
        o.write(json.dumps({c: r[c] for c in cols}, ensure_ascii=False) + "\n")
# CSV cells: Sheets limit is 50,000 chars per cell; the JSONL keeps the full text.
with open(prefix + ".csv", "w", newline="") as o:
    w = csv.DictWriter(o, fieldnames=cols); w.writeheader()
    for r in rows:
        w.writerow({c: (r[c][:49000] if isinstance(r[c], str) else r[c]) for c in cols})

v = sum(r["quote_verified"] for r in rows)
print(f"{len(rows)} rows, {v} quotes verified ({100*v/max(1,len(rows)):.0f}%), {bad} bad lines")
print("entries with at least one row:", len({r['ref'] for r in rows}), "of", len(ctx))
print("by type:", Counter(r["type"] for r in rows).most_common())
print("by source:", Counter(r["source"] for r in rows).most_common())
per = Counter(r["batch"] for r in rows); ver = Counter(r["batch"] for r in rows if r["quote_verified"])
worst = sorted(per, key=lambda b: ver[b] / per[b])[:8]
print("worst batches (verified/total):", [(b, ver[b], per[b]) for b in worst])
done = {f.rsplit("_", 1)[-1].split(".")[0] for f in glob.glob(f"{bdir}/out_b*.jsonl")}
allb = {f.rsplit("/", 1)[-1][:-4] for f in glob.glob(f"{bdir}/b*.txt")}
print("batches missing output:", sorted(allb - done))
