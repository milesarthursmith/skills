"""Check that every quoted line in a summary appears in the source conversations.

Usage: python3 -I scripts/check_quotes.py learnings.md learnings_log.jsonl
Checks text inside straight double quotes that has 4 or more words.
Prints MISSING for each quote that is not in any my_message, claude_before or claude_after.
"""
import json, re, sys

md = open(sys.argv[1]).read()
def norm(s): return re.sub(r"\s+", " ", s or "").strip().lower()
src = []
for l in open(sys.argv[2]):
    r = json.loads(l)
    src.append(norm(" ".join([r.get("my_message", ""), r.get("claude_before", ""), r.get("claude_after", "")])))
quotes = [q for q in re.findall(r'"([^"\n]{12,300})"', md) if len(q.split()) >= 4]
bad = [q for q in quotes if not any(norm(q) in s for s in src)]
for q in bad:
    print("MISSING:", q)
print(f"{len(quotes) - len(bad)} of {len(quotes)} quotes found in the source")
sys.exit(1 if bad else 0)
