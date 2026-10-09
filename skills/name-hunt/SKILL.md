---
name: name-hunt
description: "Find a name for a company, product or venture, with the founders in the loop: intake, a competitor naming scan, parallel generator subagents (one per style), collision and domain checks, a swipe-deck artifact the founders vote and comment in, a live-call pass, deeper research on the favourite direction, and a trademark pre-check. Ends with a written-up research file. Use for any naming or rename project. Run via /name-hunt [what's being named]."
---

# /name-hunt: find a name, with the founders voting

The method behind the Bloom rename (an Australian salon booking app, Sept–Oct 2026). It builds on [hunainx/startup-naming](https://github.com/hunainx/startup-naming) (MIT, see `references/LICENSE-startup-naming`). Its domain checker (`scripts/rdap.py`, extended here for .com.au and registry blocks) and references (`competitor-scan.md`, `sound-symbolism.md`, `scoring.md`, `searchability.md`, `word-banks.md`, `taglines.md`) are bundled in this folder. `SKILL_DIR` below means this folder. Differences from that skill: names come in rounds the founders steer by swiping, the domain rule is set at intake (not "exact .com or nothing"), and trademark is checked before anyone gets attached.

Keep a working folder in the scratchpad (`naming/`) with `notes.md` (brief, rules, rounds, spent words, collisions) and one `.tsv` per round. Every agent reads `notes.md`; update it after every round and every founder reaction.

## 1. Intake (one AskUserQuestion, ≤4 questions)

Read what the project already knows first (a brief, meeting notes, any existing working name) and only ask what's missing:
- **Domain rule:** exact .com, the local ccTLD (e.g. .com.au), or both. For a local-first product, the ccTLD is usually enough; short .coms are almost all taken.
- **Who must feel at home** with it (e.g. barbers *and* nail salons → gender-neutral).
- **Styles to try** (multi-select from `references/lanes.md`).
- **Hard exclusions** (an ending that echoes a competitor, tech words like -ify/AI/hub, etc.).

Write the answers to `notes.md`. Name any tension (e.g. "playful" vs "holds people's money") and get a priority.

## 2. Competitor scan + round 1 (all subagents in parallel, background)

- **One scan agent:** follow `SKILL_DIR/references/competitor-scan.md`. Get 15–20 names with the domain each actually uses, the 5-line brief (crowded / open / sound gap / spent words / domain note), and **whether the current working name is already used in the category** (for Bloom, it was).
- **3–5 lane agents**, using the template in `references/lanes.md`. Each returns 30 names plus a top 8 and writes its full raw list to a file.

## 3. Check, then load the deck

1. Curate about 40–60 names per round: drop rule breaks and known collisions, interleave the styles.
2. **.com:** `python3 SKILL_DIR/scripts/rdap.py --file com.txt` (Verisign RDAP, fast, no rate limit). Never mark a domain taken or free without a check; unchecked stays "unchecked".
3. **ccTLD:** only for finalists (≤30 per day), and see Gotchas. The fastest route is to ask a founder to type 2–3 names into a registrar's search box.
4. Write cards as TSV (`slug, Name, Style, say-it, how it's made, why it fits`). Run `python3 SKILL_DIR/scripts/seed_cards.py <round> cards.tsv com.out [au.out]` and pass each printed array to `ArtifactData` `batch`.

## 4. The swipe deck (artifact)

First round only: publish `SKILL_DIR/assets/name-swipe.html` as a claude.ai artifact (copy it to the scratchpad, set the `<title>`, e.g. "Acme Name Swipe") with:
```
capabilities: {"db": {"rules": [{"path": "votes", "read": "view", "write": "owner"},
                                {"path": "votes/{self}", "write": "interact"}]},
               "user": {"scopes": ["profile"]}}
```
Seed `names` after publishing; later rounds just add more `names` docs, with no republish needed. The page swipes right/left, has "Love it", reason chips and a note, a save-status line, an "All votes" tab showing every voter, a "Start from card 1" button, and keeps a copy of the votes in the browser.

Tell the founders:
- Share it from the page's Share menu.
- **Each voter needs Contributor access**; with Viewer access, their votes won't save.

**Read votes:** `ArtifactData list votes` (one doc per person: `v[slug] = {verdict: no|yes|love, tags, note}`). Summarise as: love / keen / nah, plus the pattern behind them (e.g. "short local -o/-ie names win; descriptive real words lose").

**Wipe votes** (e.g. before a live session):
1. Back up the docs first (`list` with `out_dir`).
2. Bump the page's browser-storage key (`"votes"` → `"votes-v2"`) and republish. Without this, a browser that still holds old votes pushes them straight back.
3. Delete each `votes/<id>` doc with its `if_version`.
4. List again to confirm it's empty.

## 5. Founders react: swipe or live call

If they go through it together on a call and paste the transcript, extract:
- the **criteria** they used (these are gold: add them to `notes.md` as rules)
- the **shortlist**, the **maybes**, and the **outs with reasons**
- any new **riffs** they coin (e.g. Kelpie, Jellie)

Write it to `call-<date>.md`. Don't make them clean up the transcript.

## 6. Deepen the favourite direction

Run the three agents in `references/lanes.md` → "Deepening a favourite": variants, research on the root (slang, other languages, existing brands, trademarks, domain holders), and the runner-up direction. Also run a **rude-reading pass** on every finalist: say it fast, read it in the target markets' main languages, look at the letters.

## 7. Trademark pre-check (before anyone gets attached)

Use one agent across the finalists. It searches the national register directly where it can (IP Australia's trade mark search worked by script on the Bloom run), filtered to the relevant classes (software 9, business 35, SaaS 42, plus the customer's own trade class, e.g. 44 for beauty). Then US/UK/EU via public mirrors, plus live unregistered use. It must:
- cite a URL for every finding
- write "no mark found via X", never "clear"
- never invent a registration number

Output: a risk table (low/med/high), names to drop, and what the founders must still do themselves:
- an Advanced (phonetic) search on the register
- a check for pending applications
- business-name and company-register lookups (e.g. ASIC/ABN in AU)
- a paid clearance search before filing

## 8. Write it up

Save `<project>-naming.md` wherever the project keeps research (ask if unclear). It covers:
- TL;DR
- the competitor scan
- founder criteria and verdicts
- the research on the favourite direction
- the trademark table
- domains
- what's still unchecked

Record the name the founders actually decide on, with the date and who decided, wherever the project logs decisions.

## Gotchas (all hit on the Bloom run)

- **ccTLD registries rate-limit hard.** auDA (`rdap.cctld.au`) answered roughly half of requests with 429, then blocked the session's IP for about 24 hours after ~50 lookups, and kept re-reporting the block a week later. `rdap.py` reads Retry-After and stops .au lookups at once. Check finalists only, or have a founder check by hand. Never loop on retries.
- **Collisions hide in the category, not the dictionary.** Check app stores and "<name> booking/software/salon" searches, not just the bare word. Sesho, the founders' favourite, turned out to be a live booking app in India. Frankie and Bloomie hit registered marks in the exact classes.
- **Slang carries shadows.** A friendly local word can have drink, drug or sex meanings (for "sesh": drinking and cannabis, documented in Cambridge and Green's). Research the root before anyone falls for it.
- **Agents can't hand back what they didn't write down.** Have lane agents save their full raw lists to a file. Asking afterwards for discards failed.
- **The deck must never wait on a save.** An early version only advanced after the database write finished, and it froze. The template now advances straight away, saves in the background, and shows a save status.
- **Don't over-ask.** One intake call; after that, let swipes and calls steer. Founders react better to cards than to questions.
