"""Download every claude.ai/code project (channel) and all its conversations.

Saves to ./web/projects/<project name>/:
  channel.json      project metadata
  timeline.json     all project posts (paged)
  threads.json      thread list
  <cse_id>.json     each conversation transcript
Then rebuilds ./web/my_messages.jsonl from ALL saved sessions + project conversations.

Run from ~/cc-transcripts:
  uv run --with "git+https://github.com/simonw/claude-code-transcripts@refs/pull/93/head" python <skill>/scripts/dump_web_projects.py  (run from your data dir)
"""
import json
import re
import time
from pathlib import Path

import httpx
from claude_code_transcripts import API_BASE_URL, fetch_session, get_api_headers, resolve_credentials

token, org = resolve_credentials(None, None)
h = get_api_headers(token, org)
h["anthropic-beta"] = "ccr-byoc-2025-07-29"
ROOT = Path("web/projects")
ROOT.mkdir(parents=True, exist_ok=True)


def get(path, **params):
    r = httpx.get(API_BASE_URL + path, headers=h, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def ids_in(v, prefix, out):
    if isinstance(v, dict):
        for x in v.values():
            ids_in(x, prefix, out)
    elif isinstance(v, list):
        for x in v:
            ids_in(x, prefix, out)
    elif isinstance(v, str) and v.startswith(prefix) and len(v) < 60:
        out.add(v)
    return out


def paged(path, key="data", **params):
    items, cursor = [], None
    for _ in range(200):
        p = dict(params)
        if cursor:
            p["cursor"] = cursor
        d = get(path, **p)
        items += d.get(key, [])
        cursor = d.get("next_cursor")
        if not cursor:
            break
    return items


# 1. List projects
chans = sorted(ids_in(get("/code/channels", scope="all"), "chan_", set()))
print(f"Found {len(chans)} projects")

failed = []
for ci, cid in enumerate(chans, 1):
    ch = get(f"/code/channels/{cid}").get("channel", {})
    name = re.sub(r"[^\w\- ]+", "_", ch.get("name") or cid).strip() or cid
    d = ROOT / name
    d.mkdir(exist_ok=True)
    (d / "channel.json").write_text(json.dumps(ch, indent=2))

    timeline = paged(f"/code/channels/{cid}/timeline", limit=50)
    (d / "timeline.json").write_text(json.dumps(timeline, indent=2))
    threads = get(f"/code/channels/{cid}/threads")
    (d / "threads.json").write_text(json.dumps(threads, indent=2))

    cses = set()
    for src in (ch, timeline, threads):
        ids_in(src, "cse_", cses)
    print(f"\n[{ci}/{len(chans)}] {name}: {len(timeline)} posts, {len(cses)} conversations")

    for sid in sorted(cses):
        path = d / f"{sid}.json"
        if path.exists():
            continue
        try:
            data = fetch_session(token, org, sid)
            try:
                data["meta"] = get(f"/sessions/{sid}")
            except Exception:
                pass
            path.write_text(json.dumps(data))
            print(f"   ok   {sid} {data.get('meta', {}).get('title', '')}")
            time.sleep(0.3)
        except Exception as ex:
            failed.append(sid)
            print(f"   FAIL {sid}: {ex}")


# 2. Rebuild my_messages.jsonl from everything saved
def user_text(entry):
    if entry.get("type") != "user":
        return None
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        parts = [content]
    elif isinstance(content, list):
        parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
    else:
        return None
    t = "\n".join(p for p in parts if p).strip()
    if not t or t.startswith(("<system-reminder", "<command-", "<local-command", "Caveat:")):
        return None
    return t


titles = {s["id"]: s.get("title", "") for s in json.loads(Path("web/index.json").read_text())}
out, n = open("web/my_messages.jsonl", "w"), 0
for f in sorted(Path("web").rglob("*.json")):
    if not f.name.startswith(("session_", "cse_")):
        continue
    data = json.loads(f.read_text())
    sid = f.stem
    project = f.parent.name if f.parent != Path("web") else None
    title = titles.get(sid) or data.get("meta", {}).get("title", "")
    for e in data.get("loglines", []):
        t = user_text(e)
        if t:
            out.write(json.dumps({"session": sid, "project": project, "title": title, "ts": e.get("timestamp"), "text": t}) + "\n")
            n += 1
out.close()

print(f"\nDone. {n} of your messages across sessions + projects -> web/my_messages.jsonl")
if failed:
    print("Failed:", ", ".join(failed))
