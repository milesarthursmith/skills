"""Save a subagent's reply that holds several output files, each under a line "FILE out_bXXX.jsonl".

Use when subagents cannot write files: save the reply text to a file, then run
  python3 -I scripts/save_reply.py reply.txt batches/
Lines before the first FILE marker are ignored. Code fences are removed.
"""
import re, sys
from pathlib import Path

text, out = Path(sys.argv[1]).read_text(), Path(sys.argv[2])
cur, buf, n = None, [], 0
def flush():
    global n
    if cur:
        lines = [l for l in buf if l.strip() and not l.strip().startswith("```")]
        (out / cur).write_text("\n".join(lines) + "\n"); n += 1
        print(f"{cur}: {len(lines)} lines")
for line in text.splitlines():
    m = re.match(r"\s*FILE\s+(out_b\d+\.jsonl)\s*$", line)
    if m:
        flush(); cur, buf = m.group(1), []
    else:
        buf.append(line)
flush()
print(n, "files saved")
