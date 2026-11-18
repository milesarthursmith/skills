"""Split messages.jsonl into text batches that read like the conversations.

Rows arrive grouped by conversation and in order (build_messages.py does this), so a batch shows a
conversation's messages one after another. Each entry shows Claude's reply before, the tool calls Claude
made, your message, and Claude's reply after.

When a batch starts or ends in the middle of a conversation, it also gets context-only blocks:
  --earlier N  the N messages before the first entry (default 3), with Claude's replies
  --later M    the M messages after the last entry (default 2), with Claude's replies
Context blocks have no "=== k=" header, so the extract does not log them a second time.

Nothing is cut. An entry larger than --size gets its own batch, split into parts.

Usage: python3 -I scripts/make_batches.py messages.jsonl batches/ [--size 80000] [--earlier 3] [--later 2]
"""
import argparse, json, textwrap
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("msgs"); ap.add_argument("outdir")
ap.add_argument("--size", type=int, default=80000)
ap.add_argument("--earlier", type=int, default=3)
ap.add_argument("--later", type=int, default=2)
a = ap.parse_args()
out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
for f in out.glob("b*.txt"):
    f.unlink()

rows = [json.loads(l) for l in open(a.msgs)]


def same(i, j):
    return 0 <= i < len(rows) and 0 <= j < len(rows) and rows[i].get("session") == rows[j].get("session")


def head(r):
    return f"=== k={r['k']} source={r['source']} date={(r.get('ts') or '')[:10]} project={r.get('project')} title={r.get('title')}\n"


def body(i, show_after=True):
    r, s = rows[i], ""
    if r.get("claude_before"):
        s += "CLAUDE BEFORE:\n" + r["claude_before"] + "\n"
    if r.get("claude_actions"):
        s += "CLAUDE DID (tool calls before this message):\n" + r["claude_actions"] + "\n"
    s += "ME:\n" + r["text"] + "\n"
    if r.get("claude_after"):
        s += ("CLAUDE AFTER: (same as next entry's CLAUDE BEFORE)\n" if not show_after
              else "CLAUDE AFTER:\n" + r["claude_after"] + "\n")
    return s


def context(idxs, label):
    if not idxs:
        return ""
    s = f"--- {label} (context only: do not log anything from this block) ---\n"
    for i in idxs:
        r = rows[i]
        s += f"[{(r.get('ts') or '')[:16]}] ME:\n{r['text']}\n"
        if r.get("claude_actions"):
            s += "CLAUDE DID:\n" + r["claude_actions"] + "\n"
        if r.get("claude_after"):
            s += "CLAUDE AFTER:\n" + r["claude_after"] + "\n"
    return s + f"--- end of {label.lower()} ---\n\n"


def wrap(s, w=900):
    """Keep every line under the Read tool's line limit. Splits at spaces, so no text is lost."""
    o = []
    for line in s.split("\n"):
        o += textwrap.wrap(line, w, break_long_words=True, break_on_hyphens=False,
                           drop_whitespace=True, replace_whitespace=False) if len(line) > w else [line]
    return "\n".join(o)


# Pack row indexes into batches by full size.
groups, cur, cur_size = [], [], 0
for i in range(len(rows)):
    n = len(head(rows[i])) + len(body(i))
    if n > a.size:
        if cur:
            groups.append(cur); cur, cur_size = [], 0
        groups.append([i]); continue
    if cur and cur_size + n > a.size:
        groups.append(cur); cur, cur_size = [], 0
    cur.append(i); cur_size += n
if cur:
    groups.append(cur)

bi, total = 0, 0
for g in groups:
    first, last = g[0], g[-1]
    pre = [j for j in range(first - a.earlier, first) if same(j, first)]
    post = [j for j in range(last + 1, last + 1 + a.later) if same(j, last)]
    parts = [context(pre, "EARLIER IN THIS CONVERSATION")]
    for i in g:
        nxt_in_batch = i + 1 in g and same(i, i + 1) and rows[i + 1].get("claude_before") == rows[i].get("claude_after")
        parts.append(head(rows[i]) + body(i, show_after=not nxt_in_batch) + "\n")
    parts.append(context(post, "LATER IN THIS CONVERSATION"))
    text = wrap("".join(parts))
    if len(g) == 1 and len(text) > a.size:  # one oversized entry: split into parts
        step = a.size - 300
        chunks = [text[j:j + step] for j in range(0, len(text), step)]
        for n, c in enumerate(chunks, 1):
            label = head(rows[g[0]]).rstrip("\n") + f" part {n}/{len(chunks)}\n" if n > 1 else ""
            (out / f"b{bi:03d}.txt").write_text(label + c)
            bi += 1; total += len(c)
        continue
    (out / f"b{bi:03d}.txt").write_text(text); bi += 1; total += len(text)
print(f"{bi} batches in {out}, {total} chars")
