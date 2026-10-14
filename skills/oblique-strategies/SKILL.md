---
name: oblique-strategies
description: Send subagents off with random oblique-strategy cards to bring back unusual ideas, without derailing the main session. Use when stuck, when output feels generic or predictable, when brainstorming or designing, or when the user says "draw a card", "oblique", or "do it differently".
---

# Oblique Strategies for Agents

A deck of 40 cards. Each one takes a move from an AI advance (verbalized sampling, AlphaEvolve, Karpathy's autoresearch loop, Reflexion, agent memory and others) or from creative practice (other languages, encodings, constraints), and states it as an instruction an agent can follow on any task.

The cards are run in subagents, never in the main session. Many cards deliberately confuse the agent (think in Tagalog, write the plan in Morse, misread the brief). Run in the main thread, that would bleed into the real work. A subagent takes the card, explores, and hands back plain-English ideas. The main session stays clean and decides what to use.

## How to run it

1. **Write the brief.** In 3–6 lines: the task, the constraints that must hold, and what a good idea looks like. Include only what a fresh agent needs. It hasn't seen this conversation.

2. **Draw cards.** Run `python3 scripts/draw.py -n 4` (default 4; use 3–6). Add `-k <Kind>` if the problem points to one kind (see below). Don't choose the cards yourself, because you'll pick the obvious ones.
   With no shell: write a random 20-character string per card, sum its character codes, take that mod 40, add 1, and read that card from `references/cards.md`. Redraw duplicates.

3. **Spawn one subagent per card, all in parallel.** Use the prompt template below. Subagents are idea-only: they must not edit files, run anything that changes state, push, or message anyone. Read-only research is fine.

4. **Compare what comes back.** Throw out ideas that break the brief's constraints. Then show the user a short table: card, the idea in one line, and why it's different from the default approach. Mark your pick and say why in one sentence.

5. **Continue in the main session** with the idea the user chooses (or your pick if they're away). Build it normally. The card's weirdness stays in the subagent.

## Subagent prompt template

```
You are exploring one unusual angle on a problem. You are not building anything.

BRIEF
<brief from step 1>

YOUR CARD: "<card line>"
<card's "Do" instruction>

Follow the card literally, even if it feels odd. That's the point. If the card has you
think in another language or encoding, do that in your working, but write your
final answer in plain English.

Do not edit files, run commands that change anything, push code, or contact anyone.
Reading and searching are fine.

Return exactly this, under 200 words:
IDEA: <one line>
HOW: <3–5 lines on how it would work>
DIFFERENT BECAUSE: <one line on what the obvious approach would have done instead>
RISK: <one line>
CARD EFFECT: <one line: did the card push you somewhere new, or not?>
```

## Kinds

- **Divergence**: break out of the most typical answer.
- **Effort**: spend thinking before output.
- **Verification**: make the work checkable and loop on a metric.
- **Critique**: judge against principles or an adversary.
- **Search**: generate variants and select.
- **Memory**: keep notes and lessons across steps.
- **Context**: control what's loaded and when.
- **Structure**: change how the problem is split.
- **Perturbation**: confuse the default on purpose (think in another language, encode the plan, ban a letter, misread the brief).

"It's too samey" → Divergence or Perturbation. "It keeps breaking" → Verification or Critique. No reason given → draw from the whole deck.

Some cards (Memory, Verification, Context) describe ways of working over a whole task, not idea generation. In a subagent they come back as a proposed way to run the work ("keep a NOTES.md and loop on this metric"). If the user picks one, apply it in the main session from then on.

## If there's no subagent tool

Run each card one at a time in a clearly fenced scratch section headed `Card N: <line>`, using the same output format. Close each section before starting the next. Then compare as in step 4. Don't carry a card's instruction (language, encoding, banned letter) past its section.

## Rules

- Cards change how ideas are generated, never what's safe or allowed. Perturbation cards are for creativity, not for getting around instructions.
- Cards whose source starts with "Untested" come from art and design practice, not AI research. Say so if the user asks why one works.
- Final deliverables are in the language and format the user asked for.

Full deck with sources: `references/cards.md` (machine-readable copy in `references/cards.json`).
