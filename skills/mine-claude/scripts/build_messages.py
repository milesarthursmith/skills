"""Build one JSONL of every message you typed to Claude, full text, with Claude's reply before and after.

Sources (column "source"):
  transcript  local Claude Code transcripts (CLI, desktop app Code tab, Claudian, other Agent SDK apps)
  queued      messages typed mid-turn in those transcripts
  web         Claude Code on the web sessions and project conversations (download first, see README)
  history     ~/.claude/history.jsonl prompts whose transcript no longer exists (your words only)
  dk          dk-mode corrections from sessions whose transcript no longer exists
  note        any notes files you name with --notes

Nothing is truncated.

Usage:
  python3 -I scripts/build_messages.py data/messages.jsonl
      [--claude-dir ~/.claude] [--web-dir ~/mine-claude-data/web] [--my-user-id user_XXXX]
      [--claudian-dir ~/vault/.claudian] [--notes "~/notes/*.md" ...] [--no-history] [--no-dk]
"""
import argparse, datetime, glob, html, json, os, re
from collections import Counter
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--claude-dir", default="~/.claude")
ap.add_argument("--web-dir", default="~/mine-claude-data/web")
ap.add_argument("--my-user-id", default=os.environ.get("MY_USER_ID", ""), help="keep only your posts in web project threads")
ap.add_argument("--claudian-dir", action="append", default=[], help="a vault's .claudian folder, for titles")
ap.add_argument("--notes", action="append", default=[], help="glob of notes files to include")
ap.add_argument("--no-history", action="store_true")
ap.add_argument("--no-dk", action="store_true")
a = ap.parse_args()

CD = Path(os.path.expanduser(a.claude_dir))
TAG_BLOCKS = re.compile(r"<(system-reminder|ide_opened_file|ide_selection|user-prompt-submit-hook|session_context|register_reminder|self-steering)[^>]*>.*?</\1>", re.S)
PASTE = re.compile(r"<pasted_content[^>]*>(.*?)</pasted_content>", re.S)
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
    t = PASTE.sub(lambda m: "\n[PASTED]\n" + m.group(1).strip() + "\n[/PASTED]\n", t).strip()
    if "<message" in t:  # web project wake: keep posts (yours only if --my-user-id)
        bodies = [html.unescape(b).strip() for at, b in MSG.findall(t)
                  if not a.my_user_id or dict(ATTR.findall(at)).get("author-id") == a.my_user_id]
        t = "\n\n".join(b for b in bodies if b)
    if not t or t.startswith(SKIP_START):
        return ""
    return t


# Titles
titles = {}
for d in a.claudian_dir:
    for f in glob.glob(os.path.join(os.path.expanduser(d), "sessions/**/*.json"), recursive=True):
        try:
            j = json.load(open(f)); titles[j["sessionId"]] = j.get("title") or ""
        except Exception:
            pass
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
                     "claude_before": ctx(i, -1), "claude_after": ctx(i, 1)})


# 1. Local transcripts
n_local = 0
for f in sorted(glob.glob(str(CD / "projects/*/*.jsonl"))):
    entries = []
    for line in open(f, errors="ignore"):
        try:
            entries.append(json.loads(line))
        except Exception:
            pass
    proj = Path(f).parent.name
    add_session(Path(f).stem, entries, proj, "transcript"); n_local += 1

# 2. Web sessions (downloaded with scripts/dump_web_*.py)
n_web = 0
for f in sorted(web_dir.rglob("*.json")) if web_dir.exists() else []:
    if not f.name.startswith(("session_", "cse_")):
        continue
    try:
        data = json.loads(f.read_text())
    except Exception:
        continue
    proj = f.parent.name if f.parent != web_dir else "web"
    add_session(f.stem, data.get("loglines", []), proj, "web"); n_web += 1

# 3. history.jsonl: prompts from sessions with no transcript left
if not a.no_history and (CD / "history.jsonl").exists():
    for line in open(CD / "history.jsonl", errors="ignore"):
        try:
            e = json.loads(line)
        except Exception:
            continue
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
                     "ts": ts, "uuid": "", "text": t, "claude_before": "", "claude_after": ""})

# 4. dk-mode corrections from sessions whose transcript is gone
short = {s[:8] for s in have_sessions}
have_text = {re.sub(r"\s+", " ", r["text"]).strip() for r in rows}  # dk often repeats a history.jsonl prompt
if not a.no_dk:
    for f in glob.glob(str(CD / "plugins/data/dk-mode*/memory/dk.jsonl")):
        for line in open(f, errors="ignore"):
            try:
                d = json.loads(line)
            except Exception:
                continue
            t, s = (d.get("user_verbatim") or "").strip(), str(d.get("session", ""))
            nt = re.sub(r"\s+", " ", t).strip()
            if not t or s[:8] in short or t.startswith(SKIP_START) or (s, t) in seen or nt in have_text:
                continue
            seen.add((s, t)); have_text.add(nt)
            rows.append({"source": "dk", "session": s, "project": d.get("cwd", ""), "title": "dk-mode correction (transcript lost)",
                         "ts": d.get("ts", ""), "uuid": d.get("uuid", ""), "text": t,
                         "claude_before": d.get("assistant_context") or "", "claude_after": ""})

# 5. Notes
for g in a.notes:
    for f in sorted(glob.glob(os.path.expanduser(g), recursive=True)):
        t = Path(f).read_text(errors="ignore").strip()
        if t:
            rows.append({"source": "note", "session": "", "project": "", "title": f, "ts": "", "uuid": "",
                         "text": t, "claude_before": "", "claude_after": ""})

rows.sort(key=lambda r: (r["source"] == "note", r["ts"] or ""))
Path(a.out).parent.mkdir(parents=True, exist_ok=True)
with open(a.out, "w") as o:
    for k, r in enumerate(rows):
        r["k"] = k
        o.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"{n_local} local transcripts, {n_web} web sessions")
print(len(rows), "rows", dict(Counter(r["source"] for r in rows)))
print("months:", sorted(Counter((r["ts"] or "none")[:7] for r in rows).items()))
