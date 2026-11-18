"""List the people who posted in your project conversations, with their account IDs.

Run from ~/cc-transcripts after dump_projects.py:
  python3 -I scripts/find_my_user_id.py web/my_messages.jsonl
Find your name and copy the user_... ID next to it.
"""
import json
import re
import sys
from collections import Counter

seen = Counter()
for line in open(sys.argv[1]):
    text = json.loads(line)["text"]
    for name, uid in re.findall(r'author="([^"]+)"[^>]*author-id="(user_[^"]+)"', text):
        seen[(name, uid)] += 1
for (name, uid), n in seen.most_common():
    print(f"{name:20} {uid}  ({n} messages)")
