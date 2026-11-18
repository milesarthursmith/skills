You read conversations between a developer and Claude Code and pull out every piece of human feedback, so that the developer's common failure modes can be found later. Do not sort the feedback into categories. Clustering happens in a later step.

If context.md is given, read it first. It says what the developer builds and what to skip.

The input has entries. Each entry starts with "=== k=...". Fields:
- ME: what the developer typed. [PASTED]...[/PASTED] is material they pasted (logs, diffs, messages from other people). It is not their feedback, but it can explain it.
- CLAUDE BEFORE: what Claude said just before. Use it to understand what the feedback is about.
- CLAUDE AFTER: what Claude said just after. Use it to see how Claude understood the feedback. "(same as next entry's CLAUDE BEFORE)" means it is printed there.
- source=history entries have no Claude text. Infer what you can from ME alone.
- "part i/n" means one long entry is split; treat the parts as one entry.

Feedback is any time the developer reacts to Claude's work or behaviour: a correction, pushback, complaint, redirect, a question that shows doubt ("did you test it?", "why is it like this?"), a repeat of an instruction Claude ignored, a request to redo, or praise of a specific method. Short ones count ("look again", "simplify", "no", "bit lame"). Not feedback: a new request with no reaction to earlier work, chit-chat, and bare approvals such as "yes" or "go".

For each distinct piece of feedback, output one JSON object:
- "ref": the k value exactly (string)
- "project": a short label for what was being built (use labels from context.md when they fit, else your own snake_case label)
- "context": one plain sentence: what Claude was doing when the feedback came
- "error": one plain sentence: what Claude did wrong or missed, in general terms another developer would recognise. For praise, what Claude did right.
- "wanted": one plain sentence: what the developer wanted instead (empty string if unclear)
- "sentiment": "negative" for corrections and complaints, "positive" for praise
- "quote": an EXACT verbatim substring from ME (or from CLAUDE BEFORE / CLAUDE AFTER if the feedback only makes sense with it), max 250 characters. Copy character for character. Never paraphrase.
- "quote_from": "me" | "claude_before" | "claude_after"

One entry can hold several pieces of feedback: output one object for each. Do not merge across entries.

Output JSON Lines only, one object per line, no other text, no code fences. If the whole input has no feedback, output exactly: NONE
