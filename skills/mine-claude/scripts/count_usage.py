"""Count skills, slash commands, subagents, MCP servers and tool errors by month. No model needed.

Usage: python3 -I count_usage.py OUT.csv
Rows: month, kind, name, count. kind = slash_command | skill_tool | subagent | mcp_server | tool_call | tool_error
"""
import csv, datetime, glob, json, re, sys
from collections import Counter
from pathlib import Path

HOME = Path.home()
c = Counter()
for f in glob.glob(str(HOME / ".claude/projects/**/*.jsonl"), recursive=True):
    sub = "/subagents/" in f
    names = {}
    for line in open(f, errors="ignore"):
        try:
            e = json.loads(line)
        except Exception:
            continue
        mo = (e.get("timestamp") or "")[:7] or "none"
        msg = e.get("message") or {}
        content = msg.get("content")
        if e.get("type") == "user" and not sub:
            t = content if isinstance(content, str) else " ".join(b.get("text", "") for b in content or [] if isinstance(b, dict) and b.get("type") == "text")
            for m in re.findall(r"<command-name>/?([^<\s]+)</command-name>", t or ""):
                c[(mo, "slash_command", m)] += 1
        if isinstance(content, list):
            for b in content:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "tool_use":
                    n = b.get("name", ""); names[b.get("id")] = n
                    inp = b.get("input") or {}
                    c[(mo, "tool_call", n)] += 1
                    if n == "Skill":
                        c[(mo, "skill_tool", str(inp.get("skill")))] += 1
                    elif n in ("Agent", "Task"):
                        c[(mo, "subagent", str(inp.get("subagent_type") or "general-purpose"))] += 1
                    elif n.startswith("mcp__"):
                        c[(mo, "mcp_server", n.split("__")[1])] += 1
                elif b.get("type") == "tool_result" and b.get("is_error"):
                    c[(mo, "tool_error", names.get(b.get("tool_use_id"), "?"))] += 1

for line in open(HOME / ".claude/history.jsonl", errors="ignore"):
    try:
        e = json.loads(line)
    except Exception:
        continue
    d = (e.get("display") or "").strip()
    if d.startswith("/"):
        mo = datetime.datetime.utcfromtimestamp(e["timestamp"] / 1000).strftime("%Y-%m") if e.get("timestamp") else "none"
        c[(mo, "slash_command_history", d.split()[0][1:])] += 1

with open(sys.argv[1], "w", newline="") as o:
    w = csv.writer(o); w.writerow(["month", "kind", "name", "count"])
    for (mo, kind, name), n in sorted(c.items()):
        w.writerow([mo, kind, name, n])
tot = Counter()
for (mo, kind, name), n in c.items():
    tot[(kind, name)] += n
for kind in ("slash_command", "slash_command_history", "skill_tool", "subagent", "mcp_server", "tool_error"):
    top = sorted(((n, name) for (k, name), n in tot.items() if k == kind), reverse=True)[:12]
    print(kind, top)
