"""Split the learnings log into project-group text files for the synthesis subagents.

Usage: python3 -I scripts/split_for_synthesis.py data/learnings_log.jsonl data/synth [--max 280000]
Groups are the largest projects, one or more per file, filled up to --max characters.
"""
import argparse, json
from collections import defaultdict
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("log"); ap.add_argument("outdir"); ap.add_argument("--max", type=int, default=280000)
a = ap.parse_args()
out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
for f in out.glob("g*.txt"):
    f.unlink()

by = defaultdict(list)
for l in open(a.log):
    x = json.loads(l)
    by[x["project"] or "other"].append(
        f"#{x['log_id']} {x['date']} [{x['project']}] {x['type']}/{x['category']} | {x['summary']} | LESSON: {x['lesson']} | Q: {x['quote'][:160]}\n")

gi, buf, names = 1, "", []
def flush():
    global gi, buf, names
    if buf:
        (out / f"g{gi}_{'_'.join(names)[:60]}.txt").write_text(buf); print(f"g{gi}", names, len(buf)); gi += 1
    buf, names = "", []
for p, lines in sorted(by.items(), key=lambda kv: -len(kv[1])):
    text = "".join(lines)
    while len(text) > a.max:  # one big project: split it
        cut = text.rfind("\n", 0, a.max) + 1
        flush(); buf, names = text[:cut], [p]; flush(); text = text[cut:]
    if buf and len(buf) + len(text) > a.max:
        flush()
    buf += text; names.append(p)
flush()
