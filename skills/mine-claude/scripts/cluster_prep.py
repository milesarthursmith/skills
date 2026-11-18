"""Prepare the clustering passes.

Pass 1 input:  python3 -I scripts/cluster_prep.py chunks feedback_log.jsonl clusters/ [--rows 500] [--seed 1]
  Writes clusters/chunk_XX.txt. Rows are shuffled (fixed seed) so each chunk mixes dates and projects.
  Each line: #log_id [project] (sentiment) context | error | wanted

Pass 2 input:  python3 -I scripts/cluster_prep.py pass2 clusters/
  Reads clusters/chunk_XX.json (pass 1 outputs) and writes clusters/pass2_input.txt:
  one line per pass-1 cluster: chunk_XX.cN | count | name | definition
"""
import argparse, json, random, re, sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("mode", choices=["chunks", "pass2"])
ap.add_argument("paths", nargs="+")
ap.add_argument("--rows", type=int, default=500)
ap.add_argument("--seed", type=int, default=1)
a = ap.parse_args()


def load_clusters(p):
    """Read a pass-1 or pass-2 output: JSON, possibly wrapped in a code fence or prose."""
    t = Path(p).read_text()
    m = re.search(r"\{.*\}", t, re.S)
    return json.loads(m.group(0))["clusters"]


if a.mode == "chunks":
    log, out = a.paths[0], Path(a.paths[1])
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("chunk_*.txt"):
        f.unlink()
    rows = [json.loads(l) for l in open(log)]
    random.Random(a.seed).shuffle(rows)
    n = 0
    for i in range(0, len(rows), a.rows):
        part = rows[i:i + a.rows]
        lines = [f"#{r['log_id']} [{r['project']}] ({r['sentiment']}) {r['context']} | {r['error']} | {r['wanted']}" for r in part]
        (out / f"chunk_{n:02d}.txt").write_text("\n".join(lines) + "\n")
        n += 1
    print(f"{n} chunks of up to {a.rows} rows in {out}")
else:
    d = Path(a.paths[0])
    lines, missing = [], []
    for f in sorted(d.glob("chunk_*.txt")):
        j = f.with_suffix(".json")
        if not j.exists():
            missing.append(f.stem); continue
        for c in load_clusters(j):
            lines.append(f"{f.stem}.{c['id']} | {len(c.get('log_ids', []))} | {c['name']} | {c.get('definition', '')}")
    (d / "pass2_input.txt").write_text("\n".join(lines) + "\n")
    print(f"{len(lines)} pass-1 clusters written to {d / 'pass2_input.txt'}")
    if missing:
        print("chunks with no pass-1 output:", missing)
