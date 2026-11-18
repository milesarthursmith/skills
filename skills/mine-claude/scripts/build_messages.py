"""Build one JSONL of every message you typed to Claude Code, full text, with Claude's reply before and after
and the tool calls Claude made in between (tool name and its main argument, first 200 characters).
Rows are grouped by conversation, in order, so batches read like the conversation.

Sources (column "source"):
  transcript  local Claude Code transcripts in <claude-dir>/projects (CLI, desktop app, Agent SDK apps)
  queued      messages typed while Claude was mid-turn, from the same files
  web         Claude Code on the web sessions and project threads (download first, see SKILL.md)
  history     <claude-dir>/history.jsonl prompts from sessions whose transcript is gone (your words only)

Nothing is truncated.

Usage:
  python3 -I scripts/build_messages.py messages.jsonl
      [--claude-dir ~/.claude] [--web-dir ~/mine-claude-data/web] [--my-user-id user_XXXX]
      [--strip-tag NAME ...] [--no-history]
      [--sources transcript,queued,web,history] [--since YYYY-MM-DD] [--until YYYY-MM-DD]
      [--include REGEX] [--exclude REGEX]

--strip-tag removes <NAME ...>...</NAME> blocks that your own hooks inject into prompts (repeatable).
--include / --exclude match the project, title and message text (case-insensitive).
"""
import argparse, datetime, glob, html, json, os, re
from collections import Counter
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--claude-dir", default="~/.claude")
ap.add_argument("--web-dir", default="~/mine-claude-data/web")
ap.add_argument("--my-user-id", default=os.environ.get("MY_USER_ID", ""), help="keep only your posts in web project threads")
ap.add_argument("--strip-tag", action="append", default=[], help="tag name your hooks inject into prompts, to remove")
ap.add_argument("--no-history", action="store_true")
ap.add_argument("--sources", default="", help="comma list of sources to keep (default: all)")
ap.add_argument("--since", default="", help="keep rows on or after this date, YYYY-MM-DD")
ap.add_argument("--until", default="", help="keep rows on or before this date, YYYY-MM-DD")
ap.add_argument("--include", default="", help="keep rows whose project, title or text matches this regex")
ap.add_argument("--exclude", default="", help="drop rows whose project, title or text matches this regex")
a = ap.parse_args()

CD = Path(os.path.expanduser(a.claude_dir))
# Blocks Claude Code itself injects into user turns, plus any the user names.
tags = ["system-reminder", "ide_opened_file", "ide_selection", "user-prompt-submit-hook"] + [re.escape(t) for t in a.strip_tag]
TAG_BLOCKS = re.compile(r"<(" + "|".join(tags) + r")\b[^>]*>.*?</\1>", re.S)
PASTE = re.compile(r"<pasted_content[^>]*>(.*?)</pasted_content>", re.S)
PASTE_OPEN = re.compile(r"<pasted_content[^>]*>")
MSG = re.compile(r"<message\b([^>]*)>(.*?)</message>", re.S)
ATTR = re.compile(r'([\w-]+)="([^"]*)"')
SKIP_START = ("<task-notification", "<local-command", "<bash-", "<command-message", "<command-name", "Caveat:",
              "This session is being continued", "[Request interrupted", "<scheduled-task", "<side-sessions-event",
              "<ci-monitor-event", "<cross-session-message", "Another Claude session sent", "<tool_use_error",
              "Base directory for this skill", "Stop hook feedback", "<wake", "<relay", "<system-note",
              "<untrusted-uploads", "Continue from where you left off")


def text_of(e):
    c = (e.get("message") or {}).get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
    return ""


def clean_user(t):
    t = TAG_BLOCKS.sub("", t or "")
    t = PASTE.sub(lambda m: "\n[PASTED]\n" + m.group(1).strip() + "\n[/PASTED]\n", t)
    t = PASTE_OPEN.sub("\n[PASTED]\n", t).replace("</pasted_content>", "\n[/PASTED]\n").strip()  # unclosed tags
    if "<message" in t:  # web project thread: keep posts (yours only if --my-user-id)
        bodies = [html.unescape(b).strip() for at, b in MSG.findall(t)
                  if not a.my_user_id or dict(ATTR.findall(at)).get("author-id") == a.my_user_id]
        t = "\n\n".join(b for b in bodies if b)
    if not t or t.startswith(SKIP_START):
        return ""
    return t


# Titles: transcript title entries, the desktop app's session files (macOS), the web index
titles = {}
for f in glob.glob(os.path.expanduser("~/Library/Application Support/Claude/claude-code-sessions/*/*/local_*.json")):
    try:
        j = json.load(open(f))
        if j.get("cliSessionId") and j.get("title"):
            titles.setdefault(j["cliSessionId"], j["title"])
    except Exception:
        pass
web_dir = Path(os.path.expanduser(a.web_dir))
if (web_dir / "index.json").exists():
    for s in json.loads((web_dir / "index.json").read_text()):
        titles.setdefault(s.get("id"), s.get("title") or "")

rows, seen, have_sessions = [], set(), set()


def add_session(sid, entries, project, src_main):
    for e in entries:
        if e.get("type") == "custom-title":
            titles[sid] = e.get("customTitle") or titles.get(sid, "")
        elif e.get("type") == "ai-title" and not titles.get(sid):
            titles[sid] = e.get("aiTitle") or ""
    have_sessions.add(sid)

    def is_user(e):
        return e.get("type") == "user" and clean_user(text_of(e))

    def actions(i):
        """Tool calls Claude made between the previous user message and entry i, oldest first."""
        out, j = [], i - 1
        while j >= 0 and not is_user(entries[j]):
            e = entries[j]
            if e.get("type") == "assistant" and isinstance((e.get("message") or {}).get("content"), list):
                calls = []
                for b in e["message"]["content"]:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        inp = b.get("input") or {}
                        arg = next((str(inp[k]) for k in ("command", "file_path", "path", "pattern", "url", "query",
                                    "description", "prompt", "skill") if inp.get(k)), "")
                        calls.append(f"{b.get('name', '?')}: {' '.join(arg.split())[:200]}")
                out = calls + out
            j -= 1
        return "\n".join(out)

    def ctx(i, step):
        parts, j = [], i + step
        while 0 <= j < len(entries):
            e = entries[j]
            if e.get("type") == "assistant" and text_of(e).strip():
                parts.append(text_of(e).strip())
            elif is_user(e):
                break
            j += step
        return "\n\n".join(reversed(parts) if step < 0 else parts)

    for i, e in enumerate(entries):
        src = None
        if e.get("type") == "user" and not e.get("isMeta") and not e.get("isSidechain"):
            t, src = clean_user(text_of(e)), src_main
        elif e.get("type") == "attachment" and (e.get("attachment") or {}).get("type") == "queued_command":
            p = e["attachment"].get("prompt")
            p = p if isinstance(p, str) else text_of({"message": {"content": p}})
            t, src = clean_user(p), "queued"
        if not src or not t or (sid, t) in seen:
            continue
        seen.add((sid, t))
        rows.append({"source": src, "session": sid, "project": project, "title": titles.get(sid, ""),
                     "ts": e.get("timestamp") or "", "uuid": e.get("uuid") or "", "text": t,
                     "claude_before": ctx(i, -1), "claude_actions": actions(i), "claude_after": ctx(i, 1)})


def load_jsonl(path):
    out = []
    for line in open(path, errors="ignore"):
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


# 1. Local transcripts
n_local = 0
for f in sorted(glob.glob(str(CD / "projects/*/*.jsonl"))):
    add_session(Path(f).stem, load_jsonl(f), Path(f).parent.name, "transcript"); n_local += 1

# 2. Web sessions
n_web = 0
for f in sorted(web_dir.rglob("*.json")) if web_dir.exists() else []:
    if not f.name.startswith(("session_", "cse_")):
        continue
    try:
        data = json.loads(f.read_text())
    except Exception:
        continue
    add_session(f.stem, data.get("loglines", []), f.parent.name if f.parent != web_dir else "web", "web"); n_web += 1

# 3. history.jsonl: prompts from sessions with no transcript left
if not a.no_history and (CD / "history.jsonl").exists():
    for e in load_jsonl(CD / "history.jsonl"):
        sid = e.get("sessionId") or ""
        if sid in have_sessions:
            continue
        t = (e.get("display") or "").strip()
        for v in (e.get("pastedContents") or {}).values():
            c = v.get("content") if isinstance(v, dict) else None
            if c:
                t += "\n[PASTED]\n" + c.strip() + "\n[/PASTED]\n"
        if not t or t.startswith(SKIP_START) or (sid, t) in seen:
            continue
        seen.add((sid, t))
        ts = datetime.datetime.utcfromtimestamp(e["timestamp"] / 1000).isoformat() + "Z" if e.get("timestamp") else ""
        rows.append({"source": "history", "session": sid, "project": e.get("project", ""), "title": "",
                     "ts": ts, "uuid": "", "text": t, "claude_before": "", "claude_actions": "", "claude_after": ""})

# Filters
keep_src = {s.strip() for s in a.sources.split(",") if s.strip()}
inc = re.compile(a.include, re.I) if a.include else None
exc = re.compile(a.exclude, re.I) if a.exclude else None


def keep(r):
    if keep_src and r["source"] not in keep_src:
        return False
    d = (r["ts"] or "")[:10]
    if d and a.since and d < a.since:
        return False
    if d and a.until and d > a.until:
        return False
    hay = " ".join(str(r.get(k) or "") for k in ("project", "title", "text"))
    return not (inc and not inc.search(hay)) and not (exc and exc.search(hay))


before = len(rows)
rows = [r for r in rows if keep(r)]
# Keep each conversation together and in order; conversations ordered by their first message.
start = {}
for r in rows:
    start[r["session"]] = min(start.get(r["session"], "~"), r["ts"] or "~")
rows.sort(key=lambda r: (start[r["session"]], r["session"], r["ts"] or ""))
Path(a.out).parent.mkdir(parents=True, exist_ok=True)
with open(a.out, "w") as o:
    for k, r in enumerate(rows):
        r["k"] = k
        o.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"{n_local} local transcripts, {n_web} web sessions")
if len(rows) != before:
    print(f"filters kept {len(rows)} of {before} rows")
print(len(rows), "rows", dict(Counter(r["source"] for r in rows)))
print("months:", sorted(Counter((r["ts"] or "none")[:7] for r in rows).items()))
