You merge failure-mode clusters that were found separately in several chunks of one developer's feedback to Claude Code.

Each input line is one chunk cluster:
chunk_id.cluster_id | row count | name | definition

Merge clusters that describe the same underlying failure (or good practice) into one final cluster. Keep clusters apart when a single rule could not cover both. Keep positive practices apart from failures.

Rules:
- Every input cluster id goes in exactly one final cluster's "members".
- Aim for 12 to 40 final clusters. Merge the "Other" clusters into a final "Other" unless they match a real cluster.
- Name: at most 8 words, plain, describing the behaviour.
- Definition: one sentence a reviewer could apply to a new case.
- Rule: one sentence telling an agent or reviewer what to do instead (for failures) or to keep doing (for good practices).

Output one JSON object and nothing else:
{"clusters": [{"name": "...", "definition": "...", "rule": "...", "members": ["chunk_00.c1", "chunk_03.c7"]}]}
