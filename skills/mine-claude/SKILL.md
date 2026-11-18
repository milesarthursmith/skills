---
name: mine-claude
description: Mine your own Claude conversations for what you learnt. Reads local Claude Code transcripts (CLI, desktop app, Claudian, Agent SDK apps), Claude Code on the web sessions, history.jsonl and dk-mode. Logs every failure, correction, lesson, skill used and tool limit with an exact quote, checks each quote against the source, and writes a short learnings summary. Use when the user says "mine my Claude conversations", "what have I learnt from Claude", "failure log", "lessons from my sessions", or wants a retro on how they work with Claude.
---

# mine-claude

Turns months of Claude conversations into one log and one summary. The log has a row per item (failure, correction, lesson, skill_used, what_worked, tool_limit), each with an exact quote. A script checks every quote against the source text. Haiku reads the conversations, Sonnet groups the rows into themes, and you write the summary from those themes.

`SKILL` below means this skill's folder. `DATA` means `~/mine-claude-data` unless the user names another place. Keep `DATA` out of git and cloud sync: transcripts hold anything pasted into chats, keys included. Never print or copy a credential you see in a transcript.

## What it reads

| Source | Where | Has Claude's replies |
|---|---|---|
| Local transcripts | `~/.claude/projects/*/*.jsonl` | Yes, full |
| Messages typed mid-turn | Same files | Yes |
| Claude Code on the web | Downloaded to `DATA/web` (step 2) | Yes |
| Prompts from deleted transcripts | `~/.claude/history.jsonl` | No |
| dk-mode corrections | `~/.claude/plugins/data/dk-mode*/memory/dk.jsonl` | A short part |
| Notes | Any files the user names | n/a |

It does not read claude.ai chats, screenshots or subagent transcripts. Nothing is truncated.

## Steps

**0. Check retention.** Claude Code deletes local transcripts after 30 days unless `cleanupPeriodDays` is set in `~/.claude/settings.json`. Read the file. If the setting is missing, tell the user what is at risk and offer to set it to 3650. Do not change the file without a yes.

**1. Set up `DATA`.** `mkdir -p ~/mine-claude-data`. Write `DATA/context.md` from `SKILL/context.example.md`. Ask the user two things only if you cannot infer them from the conversation or memory: one line on what they work on, and the project labels to use.

**2. Web sessions (ask first).** Only if the user uses Claude Code on the web. This uses private Anthropic endpoints through a patched `claude-code-transcripts` (the published one is broken, issue #77; PR #93 fixes it), so it can break without notice. It needs `uv` and a Claude Code login. Run from `DATA`:

```bash
cd ~/mine-claude-data
uv run --with "git+https://github.com/simonw/claude-code-transcripts@refs/pull/93/head" python SKILL/scripts/dump_web_sessions.py
uv run --with "git+https://github.com/simonw/claude-code-transcripts@refs/pull/93/head" python SKILL/scripts/dump_web_projects.py
python3 -I SKILL/scripts/find_my_user_id.py web/my_messages.jsonl
```

Both download scripts skip files already saved. One 403 is normal. The last command lists posters in project threads: ask the user which `user_...` ID is theirs.

**3. Build messages and batches.**

```bash
python3 -I SKILL/scripts/build_messages.py DATA/messages.jsonl [--my-user-id user_XXXX] [--claudian-dir <vault>/.claudian] [--notes "<glob>"]
python3 -I SKILL/scripts/make_batches.py DATA/messages.jsonl DATA/batches
```

`--claudian-dir` adds Claudian titles (repeatable). `--notes` adds lesson files such as memory or retro notes (repeatable). Show the user the row counts by source and month. Months with only `history` rows mean the full transcripts were deleted. Say so.

**4. Extract with Haiku.** Tell the user the batch count first. As a guide, 5,000 messages make about 125 batches of 80 KB.

Route A (fast). Check `claude -p --model haiku "say ok"` works. If it does:

```bash
python3 -I SKILL/scripts/run_extract.py DATA/batches SKILL/prompts/extract.md --workers 6
```

Route B (no headless login). Launch `general-purpose` subagents with `model: haiku`, 3 batches each, up to 10 at a time. Start a new one as each finishes. Prompt:

```
Read SKILL/prompts/extract.md and DATA/context.md (absolute paths). Follow the instructions
for each input file, one at a time. Read each input file completely in chunks of 300 lines
with the Read tool's offset and limit; if a chunk is over the size limit use allow_large or
smaller chunks. Do not skip any part. Do not use Bash.
Inputs: DATA/batches/bXXX.txt -> DATA/batches/out_bXXX.jsonl (absolute paths).
Write each output with the Write tool. If the Write tool refuses, reply with the full JSON
Lines under a line "FILE out_bXXX.jsonl". Quotes must be exact copies of input text. Do not
copy any credentials. Otherwise reply only with line counts.
```

If an agent replies with JSON Lines instead of writing them, save them to the named file yourself.

**5. Merge and check quotes.**

```bash
python3 -I SKILL/scripts/merge.py DATA/messages.jsonl DATA/batches DATA/learnings_log
```

It writes `learnings_log.jsonl` and `.csv`. It also prints the verified-quote rate, the worst batches and any batch with no output. Rerun missing batches once. Below 95% verified, look at the worst batches before going on.

**6. Group into themes with Sonnet.**

```bash
python3 -I SKILL/scripts/split_for_synthesis.py DATA/learnings_log.jsonl DATA/synth
```

Launch one `general-purpose` subagent with `model: sonnet` for each `DATA/synth/g*.txt`, all at once:

```
Read the whole file <path> in chunks (offset/limit; allow_large if needed). Each line is:
#log_id date [project] type/category | summary | LESSON | Q: quote.
Group the rows into themes. Merge rows that teach the same thing. Rank by row count.
For each theme give: a rule in one plain sentence; the row count, date range, and whether
it kept happening after it was first logged; 2 or 3 log_ids; one quote copied exactly from
a Q: field. Then list tool and platform limits worth keeping (one line each, with a log_id)
and things that worked (one line each, with a log_id). Plain English, short sentences.
Max about 1,200 words. Return the report as text.
```

**7. Write the summary.** Write `DATA/learnings.md` (or where the user wants it). Order:
1. The few rules that appear in most groups, each with one quote and a rough item count.
2. A short section for each group.
3. Platform limits, what worked, and usage (step 8).
4. Coverage: date range of full text, range with history only, anything lost, and where the log is.

Then verify the quotes:

```bash
python3 -I SKILL/scripts/check_quotes.py DATA/learnings.md DATA/learnings_log.jsonl
```

Fix or drop every quote it reports as MISSING.

**8. Usage counts (no model).**

```bash
python3 -I SKILL/scripts/count_usage.py DATA/usage_by_month.csv
```

Counts slash commands, skills, subagents, MCP servers and tool errors by month, from local transcripts.

## Two machines

Run steps 1 to 5 on each. Copy the other machine's `learnings_log.jsonl` across by hand (not through git), then:

```bash
python3 -I SKILL/scripts/combine_logs.py DATA/learnings_log_all.jsonl work=DATA/learnings_log.jsonl home=<path>/learnings_log.jsonl
```

Run steps 6 and 7 on the combined file.

## Notes

- Lost transcripts cannot be rebuilt. Before you call something lost, check `history.jsonl`, dk-mode, migration backups and any Claudian or app folders. Claudian keeps only titles and resumes from Claude Code's own transcripts.
- Report the verified-quote rate with the results. A row whose quote does not match is marked `quote_verified=false`. It is not deleted.
- The `k` reference in each row points back to `DATA/messages.jsonl`, which holds the full message and Claude's replies on each side.
