# Generator lanes

One subagent per lane, all in parallel. Pick 3–5 lanes per round from what the intake and the competitor scan point at; later rounds come from what the founders liked. Every lane prompt uses the template at the bottom.

The examples are from the Bloom run (an AU salon booking app, 2026). Swap them for the new project's world.

| Lane | What it makes | Bloom examples that landed |
|---|---|---|
| **Bouncy coinage** | Made-up, 1–2 syllables, double letters, -le/-y/-o/-ie tails (the Bopple shape) | Choppo, Chopple |
| **Warped real word** | A real word from the customer's world, clipped, re-spelled or with a tail added (Canva from canvas) | Parlo (parlour), Kempy |
| **Human first name** | Sounds like a friendly person on the team (Heidi, Oscar, Olive); works for any gender; hidden meaning is a bonus | Frankie |
| **Local slang twist** | The market's own slang, clipped the local way. Check every word for a crude or drug/drink meaning | Sesho, Seshie, Righto |
| **Growth / job / business** | The customer's job-to-be-done, the owner's world (the till, regulars, opening up), growth | Shingo, Chimo, Rocko |
| **Double meaning** | One word carrying two meanings, one from the trade and one from the business result | Regrowie, Goodnick, Bobsy |
| **Happy sounds** | Onomatopoeia and sound-play (pop, boop, ping, fizz) | Bopchop, Popkin |
| **Cute and round** | Soft, round, tactile things (bubbles, beans, buttons) | Sudso, Fluffle |
| **Local cute** | Things only that country has: animals, foods, objects, clipped | Possie, Pavvy |
| **Everyday object** | An ordinary, comfy, slightly daggy object with no link to the category (Tracksuit, Apple) | Scrunchie, Teacosy |

## Lane prompt template

```
Brand-name generation, round <N>. Read <notes.md> fully: the brief, all earlier rounds, spent words,
names already used, known collisions, and what the founders liked and disliked. Also read
SKILL_DIR/references/sound-symbolism.md.

Lane: <LANE NAME>. <2–4 sentences: what the lane is, raw material to mine, the feeling to hit,
and the register: e.g. "cute-cool like Bopple, never babyish">.

Rules: <the hard exclusions from intake: endings, tech words, gender, phone test>. Not crude or
slang-risky: flag any risk plainly, never hide it. Not in the used or collision lists.

Process: brainstorm ~100, keep your best 30, WebSearch your top 10 for existing brands (especially
in <the category>, payments and SaaS) and drop clashes. Don't check domains; that's done centrally.

Write ALL your raw candidates, including the ones you cut and why (capacity / weak / rule /
slang-risk / collision: name it), to <dir>/raw-<lane>.tsv BEFORE you reply.

Output ONLY: 30 lines `name | how it's made | why it fits`, then `TOP 8:`, then
`Dropped after search:` with reasons.
```

The "write all raw candidates to a file" line matters. On the Bloom run, agents asked afterwards for their discards were blocked: the discards lived only in their private working notes, and about 350 names were lost. Ask for the file up front.

## Deepening a favourite

When founders pick a direction (e.g. "some adaptation of sesh"), run three agents at once:

1. **Variants:** endings, spellings, compounds, local twists on the root; cut to 20; collision-check the top 10.
2. **Research the root:** dictionary and slang meanings in each target market (cite sources); meanings in other languages; existing brands and apps using it; trademarks; who holds the exact domains.
3. **The runner-up direction**, done the same way, so there's a real alternative.
