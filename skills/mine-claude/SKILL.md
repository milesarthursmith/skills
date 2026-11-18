---
name: mine-claude
description: Mine the human feedback in your Claude Code conversations and cluster it into the failure modes that keep coming back when you build software. Pulls every correction, pushback and complaint from your transcripts with its context and an exact quote, lets AI find the clusters (no preset categories), and turns them into rules for code review tools such as CodeRabbit, CLAUDE.md, hooks, coding-agent prompts or evals. Use when the user says "mine my Claude conversations", "find my common failure modes", "what does Claude keep getting wrong", "turn my corrections into rules", or wants review rules or guardrails built from real feedback.
---

# mine-claude

Every time you correct Claude Code, you write down a failure mode. This skill collects those corrections from your transcripts, works out what Claude was doing and what went wrong, and clusters them so the repeat failures stand out. Each cluster comes with a rule you can put where it will stop the failure: a review tool, CLAUDE.md, a hook, an agent prompt or an eval.

Three stages:
1. **Collect.** Scripts read every message you typed, with Claude's reply before and after. Nothing is cut.
2. **Understand.** Haiku reads each exchange. For every piece of feedback it writes the context, the error, what you wanted, and an exact quote. A script checks each quote against the source.
3. **Cluster.** Sonnet groups the feedback into failure modes found in the data, in two passes (per chunk, then merged). A script assigns every row to a cluster and counts them.

`SKILL` means this skill's folder. `DATA` means `~/mine-claude-data` unless the user names another place. Keep `DATA` out of git and cloud sync: transcripts hold anything pasted into chats, keys included. Never print or copy a credential you see in a transcript.

## Sources

| Source | Where | Claude's replies |
|---|---|---|
| Local transcripts | `~/.claude/projects/*/*.jsonl` (CLI, desktop app, Agent SDK apps) | Full |
| Messages typed mid-turn | Same files | Full |
| Claude Code on the web | Downloaded to `DATA/web` (step 2) | Full |
| Prompts from deleted transcripts | `~/.claude/history.jsonl` | None |

## Steps

**0. Check retention.** Claude Code deletes local transcripts after 30 days unless `cleanupPeriodDays` is set in `~/.claude/settings.json`. Read the file. If the setting is missing, tell the user how much history is at risk and offer to set it to 3650. Change the file only after a yes.

**1. Agree the scope.** `mkdir -p ~/mine-claude-data`. Ask in one message, offering the defaults in brackets, and skip anything the request already answers:
- Sources (all available).
- Date range (all time).
- Projects or repos to include or skip (all).
- Tags your own hooks inject into prompts, if any (none). Check a few recent prompts in a transcript for `<tag>` blocks that are not Claude Code's own.
- What they want at the end (clusters; or clusters plus rules for one target, see step 7).

Write `DATA/context.md` from `SKILL/context.example.md`: what they build, project labels if they have them, and what to skip.

**2. Web sessions (only if they use Claude Code on the web; ask first).** This uses Anthropic endpoints that are not public, through a patched `claude-code-transcripts` (PR #93 fixes the published version's issue #77). It can stop working without notice. Needs `uv` and a Claude Code login. Run from `DATA`:

```bash
cd ~/mine-claude-data
uv run --with "git+https://github.com/simonw/claude-code-transcripts@refs/pull/93/head" python SKILL/scripts/dump_web_sessions.py
uv run --with "git+https://github.com/simonw/claude-code-transcripts@refs/pull/93/head" python SKILL/scripts/dump_web_projects.py
python3 -I SKILL/scripts/find_my_user_id.py web/my_messages.jsonl
```

The download scripts skip files already saved. One 403 is normal. The last command lists posters in shared project threads: ask which `user_...` ID is the user's.

**3. Collect.**

```bash
python3 -I SKILL/scripts/build_messages.py DATA/messages.jsonl [--my-user-id user_XXXX] [--strip-tag NAME ...] \
  [--sources transcript,queued,web,history] [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--include REGEX] [--exclude REGEX]
python3 -I SKILL/scripts/make_batches.py DATA/messages.jsonl DATA/batches
```

Show the row counts by source and month. Months with only `history` rows mean the transcripts were deleted: say so.

**4. Understand (Haiku).** Tell the user the batch count first. As a guide, 5,000 messages make about 125 batches of 80 KB.

Route A, if `claude -p --model haiku "say ok"` works:

```bash
python3 -I SKILL/scripts/run_extract.py DATA/batches SKILL/prompts/extract.md --context DATA/context.md --workers 6
```

Route B, otherwise: `general-purpose` subagents with `model: haiku`, 3 batches each, up to 10 at a time, starting a new one as each finishes. Prompt:

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
python3 -I SKILL/scripts/merge.py DATA/messages.jsonl DATA/batches DATA/feedback_log
```

Rerun any batch listed as missing output. Below 95% verified quotes, inspect the worst batches before you go on.

**6. Cluster (Sonnet, two passes).**

```bash
python3 -I SKILL/scripts/cluster_prep.py chunks DATA/feedback_log.jsonl DATA/clusters
```

Pass 1: one `general-purpose` subagent with `model: sonnet` per `DATA/clusters/chunk_XX.txt`, all at once:

```
Read SKILL/prompts/cluster_pass1.md, then read all of <chunk path> (offset/limit chunks;
allow_large if needed). Follow the instructions. Return only the JSON object.
```

Save each reply to `DATA/clusters/chunk_XX.json`. Then:

```bash
python3 -I SKILL/scripts/cluster_prep.py pass2 DATA/clusters
```

Pass 2: one `general-purpose` subagent with `model: sonnet`:

```
Read SKILL/prompts/cluster_pass2.md, then read all of DATA/clusters/pass2_input.txt.
Follow the instructions. Return only the JSON object.
```

Save the reply to `DATA/clusters/final.json`. Then:

```bash
python3 -I SKILL/scripts/cluster_apply.py DATA/feedback_log.jsonl DATA/clusters DATA/feedback
```

If more than 2% of rows are unassigned or not merged, rerun the pass-1 chunks they came from. Show the user the top clusters with row counts, the date range of each, and how many months each was seen. A cluster seen across many months is a failure that a rule has not fixed.

**7. Rules for a target (only if asked).** For each cluster the user picks (default: the negative clusters seen in 3 or more months), write the cluster's rule in the target's format, with its row count and one verified quote as evidence:
- Code review tool: instructions by file path (for CodeRabbit, `reviews.path_instructions` in `.coderabbit.yaml`) for failures that show in a diff, such as a missing test, a migration with no rollback, or an unchecked write.
- CLAUDE.md: one line per rule, for failures in how Claude works (claims done without running tests, edits the wrong branch).
- Hook: a check a script can run before or after a tool call (for example, block `git push` to main, block writes outside the repo).
- Coding-agent prompt: a short "Known failure modes" block: what it looks like, what to do instead.
- Evals: one test case per cluster, built from a quoted exchange.

Write the drafts to `DATA/rules.md`, then check the quotes:

```bash
python3 -I SKILL/scripts/check_quotes.py DATA/rules.md DATA/feedback_log.jsonl
```

Fix or drop every quote reported as MISSING. Show the drafts. Change no project file without a yes.

**8. Usage counts (optional, no model).**

```bash
python3 -I SKILL/scripts/count_usage.py DATA/usage_by_month.csv
```

Counts slash commands, skills, subagents, MCP servers and tool errors by month.

## Two machines

Run steps 1 to 5 on each machine. Copy the other machine's `feedback_log.jsonl` across by hand (not through git), then:

```bash
python3 -I SKILL/scripts/combine_logs.py DATA/feedback_log_all.jsonl work=DATA/feedback_log.jsonl home=<path>/feedback_log.jsonl
```

Run steps 6 and 7 on the combined file.

## Notes

- Report the verified-quote rate with every result. Rows whose quote does not match stay in the log with `quote_verified=false`.
- `ref` (k=N) in each row points to `DATA/messages.jsonl`, which holds the full message and Claude's replies on each side.
- Lost transcripts cannot be rebuilt. Before you call a period lost, check `history.jsonl` and any backups the user has.
