"""Split messages.jsonl into text batches. Nothing is cut: an entry larger than the batch size is split into parts.

Usage: python3 -I scripts/make_batches.py data/messages.jsonl data/batches [--size 80000]
"""
import argparse, json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("msgs"); ap.add_argument("outdir"); ap.add_argument("--size", type=int, default=80000)
a = ap.parse_args()
out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
for f in out.glob("b*.txt"):
    f.unlink()

rows = [json.loads(l) for l in open(a.msgs)]
blocks = []
for i, r in enumerate(rows):
    head = f"=== k={r['k']} source={r['source']} date={(r.get('ts') or '')[:10]} project={r.get('project')} title={r.get('title')}\n"
    body = ""
    if r.get("claude_before"):
        body += "CLAUDE BEFORE:\n" + r["claude_before"] + "\n"
    body += ("NOTE:\n" if r["source"] == "note" else "ME:\n") + r["text"] + "\n"
    nxt = rows[i + 1] if i + 1 < len(rows) else None
    if r.get("claude_after"):
        if nxt and nxt.get("session") == r.get("session") and nxt.get("claude_before") == r["claude_after"]:
            body += "CLAUDE AFTER: (same as next entry's CLAUDE BEFORE)\n"
        else:
            body += "CLAUDE AFTER:\n" + r["claude_after"] + "\n"
    if len(head) + len(body) <= a.size:
        blocks.append(head + body + "\n")
    else:
        step = a.size - 300
        parts = [body[j:j + step] for j in range(0, len(body), step)]
        for n, p in enumerate(parts, 1):
            blocks.append(head.rstrip("\n") + f" part {n}/{len(parts)}\n" + p + "\n\n")

import textwrap
def wrap(s, w=900):
    """Keep every line under the Read tool's line limit. Splits at spaces, so no text is lost."""
    out = []
    for line in s.split("\n"):
        out += textwrap.wrap(line, w, break_long_words=True, break_on_hyphens=False,
                             drop_whitespace=True, replace_whitespace=False) if len(line) > w else [line]
    return "\n".join(out)
blocks = [wrap(b) for b in blocks]

bi, buf = 0, ""
def flush():
    global bi, buf
    if buf:
        (out / f"b{bi:03d}.txt").write_text(buf); bi += 1; buf = ""
for b in blocks:
    if buf and len(buf) + len(b) > a.size:
        flush()
    buf += b
flush()
print(f"{bi} batches in {out}, {sum(len(b) for b in blocks)} chars")
