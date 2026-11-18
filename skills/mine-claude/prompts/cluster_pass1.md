You group a developer's feedback to Claude Code into failure modes. No category list is given: find the groups in the data.

Each input line is one piece of feedback:
#log_id [project] (sentiment) context | error | wanted

Group lines that describe the same underlying failure (or, for positive lines, the same good practice), even when the project or wording differs. A good cluster is one a developer would recognise and could write a single rule for, such as "claims a fix works without running it" or "edits files outside the task". Prefer the cause over the symptom. Keep positive and negative lines in separate clusters.

Rules:
- Every log_id in the input goes in exactly one cluster.
- Aim for 10 to 30 clusters. A cluster needs at least 2 lines; put single lines that fit nothing in one cluster named "Other".
- Name: at most 8 words, plain, describing the behaviour. Definition: one sentence a reviewer could apply to a new case.

Output one JSON object and nothing else:
{"clusters": [{"id": "c1", "name": "...", "definition": "...", "log_ids": [12, 40, 77]}]}
