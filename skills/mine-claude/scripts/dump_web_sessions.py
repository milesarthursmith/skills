"""Download every Claude Code on the web session to ./web/, plus a file of just your messages.

Run from ~/cc-transcripts:
  uv run --with "git+https://github.com/simonw/claude-code-transcripts@refs/pull/93/head" python <skill dir>/scripts/dump_web_sessions.py   (run from your data dir)
"""
import json
import time
from pathlib import Path

import httpx
from claude_code_transcripts import (
    API_BASE_URL,
    fetch_session,
    get_api_headers,
    resolve_credentials,
)

OUT = Path("web")  # run from your data dir, for example ~/mine-claude-data
OUT.mkdir(parents=True, exist_ok=True)

token, org = resolve_credentials(None, None)
headers = get_api_headers(token, org)
headers["anthropic-beta"] = "ccr-byoc-2025-07-29"

# 1. List all sessions, following pagination if the API returns it.
sessions, params = [], {"limit": 100}
while True:
    r = httpx.get(f"{API_BASE_URL}/sessions", headers=headers, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    page = data.get("data", [])
    sessions += page
    nxt = data.get("next_cursor") or (data.get("last_id") if data.get("has_more") else None)
    if not page or not nxt:
        break
    params = {"limit": 100, "after_id": nxt} if "last_id" in data else {"limit": 100, "cursor": nxt}

(OUT / "index.json").write_text(json.dumps(sessions, indent=2))
print(f"Found {len(sessions)} sessions")


# 2. Fetch each transcript.
def user_text(entry):
    """Return text you typed in this entry, or None (skips tool results and system noise)."""
    if entry.get("type") != "user":
        return None
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        parts = [content]
    elif isinstance(content, list):
        parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
    else:
        return None
    text = "\n".join(p for p in parts if p).strip()
    if not text or text.startswith(("<system-reminder", "<command-", "<local-command", "Caveat:")):
        return None
    return text


mine, failed = [], []
for i, s in enumerate(sessions, 1):
    sid, title = s.get("id"), s.get("title", "")
    path = OUT / f"{sid}.json"
    try:
        if path.exists():
            data = json.loads(path.read_text())
        else:
            data = fetch_session(token, org, sid)
            path.write_text(json.dumps(data))
            time.sleep(0.3)
        for e in data.get("loglines", []):
            t = user_text(e)
            if t:
                mine.append({"session": sid, "title": title, "ts": e.get("timestamp"), "text": t})
        print(f"[{i}/{len(sessions)}] ok   {title}")
    except Exception as ex:
        failed.append(sid)
        print(f"[{i}/{len(sessions)}] FAIL {title}: {ex}")

with open(OUT / "my_messages.jsonl", "w") as f:
    for m in mine:
        f.write(json.dumps(m) + "\n")

print(f"\nSaved {len(sessions) - len(failed)} sessions, {len(mine)} of your messages -> web/my_messages.jsonl")
if failed:
    print("Failed:", ", ".join(failed))
