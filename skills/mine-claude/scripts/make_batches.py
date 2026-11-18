"""Split messages.jsonl into batches of whole conversations.

The unit is a conversation, not a message. build_messages.py keeps each conversation's rows together and
in order. A batch holds one or more whole conversations. Each entry shows Claude's reply before, the tool
calls Claude made, your message, and Claude's reply after, so the batch reads like the conversation.

A conversation larger than --size is split into parts. Each part after the first starts with an overview
of the conversation so far (context only, not logged again):
  - the title and your opening message
  - an outline: one line per earlier message of yours (first 200 characters, last 100 messages)
  - the last --earlier exchanges (default 3)
Context blocks cap each message at 3,000 characters. The entries themselves are never cut.
Each part before the last ends with the next --later messages (default 2), also context only.

Nothing in the entries is cut. A single message larger than --size gets its own batch, split into parts.

Usage: python3 -I scripts/make_batches.py messages.jsonl batches/ [--size 150000] [--earlier 3] [--later 2]
"""
import argparse, json, textwrap
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("msgs"); ap.add_argument("outdir")
ap.add_argument("--size", type=int, default=150000)
ap.add_argument("--earlier", type=int, default=3)
ap.add_argument("--later", type=int, default=2)
a = ap.parse_args()
out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
for f in out.glob("b*.txt"):
    f.unlink()

rows = [json.loads(l) for l in open(a.msgs)]


def oneline(s, n=200):
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[:n] + "..."


def head(r):
    return f"=== k={r['k']} source={r['source']} date={(r.get('ts') or '')[:10]} project={r.get('project')} title={r.get('title')}\n"


def entry(i, show_after):
    r, s = rows[i], head(rows[i])
    if r.get("claude_before"):
        s += "CLAUDE BEFORE:\n" + r["claude_before"] + "\n"
    if r.get("claude_actions"):
        s += "CLAUDE DID (tool calls before this message):\n" + r["claude_actions"] + "\n"
    s += "ME:\n" + r["text"] + "\n"
    if r.get("claude_after"):
        s += ("CLAUDE AFTER: (same as next entry's CLAUDE BEFORE)\n" if not show_after
              else "CLAUDE AFTER:\n" + r["claude_after"] + "\n")
    return s + "\n"


CTX_CAP = 3000  # context blocks only; the entries themselves are never cut


def cap(s, n=CTX_CAP):
    s = s or ""
    return s if len(s) <= n else s[:n] + f"\n[... {len(s) - n} more characters; full text is in the entry itself]"


def exchanges(idxs):
    s = ""
    for i in idxs:
        r = rows[i]
        s += f"[{(r.get('ts') or '')[:16]}] ME:\n{cap(r['text'])}\n"
        if r.get("claude_actions"):
            s += "CLAUDE DID:\n" + cap(r["claude_actions"]) + "\n"
        if r.get("claude_after"):
            s += "CLAUDE AFTER:\n" + cap(r["claude_after"]) + "\n"
    return s


def overview(conv, first_idx):
    """Context-only block for a part that starts mid-conversation."""
    pos = conv.index(first_idx)
    start = conv[0]
    s = "--- CONVERSATION SO FAR (context only: do not log anything from this block) ---\n"
    s += f"Title: {rows[start].get('title') or '(none)'}\n"
    s += "Opening message:\n" + exchanges([start])
    recent = conv[max(1, pos - a.earlier):pos]
    middle = conv[1:max(1, pos - a.earlier)]
    if middle:
        shown = middle[-100:]
        s += "Outline of the messages in between (one line each):\n"
        if len(middle) > len(shown):
            s += f"- ({len(middle) - len(shown)} earlier messages not listed)\n"
        s += "".join(f"- [{(rows[i].get('ts') or '')[:16]}] {oneline(rows[i]['text'])}\n" for i in shown)
    if recent:
        s += "Most recent exchanges before this part:\n" + exchanges(recent)
    return s + "--- end of conversation so far ---\n\n"


def cut_start(conv):
    """Context block when a filter removed the start of the conversation."""
    o = rows[conv[0]].get("session_opening")
    if not o:
        return ""
    return ("--- HOW THIS CONVERSATION STARTED (before the selected range; context only: do not log) ---\n"
            f"Title: {rows[conv[0]].get('title') or '(none)'}\n[{(o.get('ts') or '')[:16]}] ME:\n{cap(o['text'])}\n"
            + (f"CLAUDE AFTER:\n{cap(o['claude_after'])}\n" if o.get("claude_after") else "")
            + "--- end of how this conversation started ---\n\n")


def later(conv, last_idx):
    pos = conv.index(last_idx)
    nxt = conv[pos + 1:pos + 1 + a.later]
    if not nxt:
        return ""
    return ("--- LATER IN THIS CONVERSATION (context only: do not log anything from this block) ---\n"
            + exchanges(nxt) + "--- end of later in this conversation ---\n\n")


def wrap(s, w=900):
    """Keep every line under the Read tool's line limit. Splits at spaces, so no text is lost."""
    o = []
    for line in s.split("\n"):
        o += textwrap.wrap(line, w, break_long_words=True, break_on_hyphens=False,
                           drop_whitespace=True, replace_whitespace=False) if len(line) > w else [line]
    return "\n".join(o)


# Conversations: contiguous runs of the same session.
convs = []
for i, r in enumerate(rows):
    if convs and rows[convs[-1][0]].get("session") == r.get("session"):
        convs[-1].append(i)
    else:
        convs.append([i])


def render(conv, idxs):
    """Text for a run of entries from one conversation, with context blocks if it is a part."""
    s = cut_start(conv) + (overview(conv, idxs[0]) if idxs[0] != conv[0] else "")
    for i in idxs:
        nxt = i + 1 in idxs and rows[i + 1].get("claude_before") == rows[i].get("claude_after")
        s += entry(i, show_after=not nxt)
    if idxs[-1] != conv[-1]:
        s += later(conv, idxs[-1])
    return s


units = []  # (text, conversation, is_whole)
for conv in convs:
    whole = render(conv, conv)
    if len(whole) <= a.size:
        units.append(whole); continue
    part = []  # split a long conversation into parts that each fit
    for i in conv:
        trial = render(conv, part + [i])
        if part and len(trial) > a.size:
            units.append(render(conv, part)); part = [i]
        else:
            part.append(i)
    if part:
        units.append(render(conv, part))

bi, total, buf = 0, 0, ""


def write(text):
    global bi, total
    text = wrap(text)
    if len(text) > a.size:  # one oversized message: split into labelled parts
        step = a.size - 300
        chunks = [text[j:j + step] for j in range(0, len(text), step)]
        for n, c in enumerate(chunks, 1):
            label = f"(part {n}/{len(chunks)} of one long entry; treat the parts as one entry)\n" if n > 1 else ""
            (out / f"b{bi:03d}.txt").write_text(label + c); bi += 1; total += len(c)
        return
    (out / f"b{bi:03d}.txt").write_text(text); bi += 1; total += len(text)


for u in units:
    if buf and len(buf) + len(u) > a.size:
        write(buf); buf = ""
    buf += u
if buf:
    write(buf)
split = sum(1 for c in convs if len(render(c, c)) > a.size)
print(f"{bi} batches in {out}, {total} chars; {len(convs)} conversations, {split} split into parts")
