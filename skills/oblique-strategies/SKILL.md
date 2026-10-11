---
name: oblique-strategies
description: Draw a random oblique-strategy card to push an agent off its default approach. Use when stuck, when output feels generic or predictable, when brainstorming or designing, or when the user says "draw a card", "oblique", or "do it differently".
---

# Oblique Strategies for Agents

A deck of 40 cards. Each one takes a move from an AI advance (verbalized sampling, AlphaEvolve, Karpathy's autoresearch loop, Reflexion, agent memory and others) or from creative practice (other languages, encodings, constraints), and states it as an instruction an agent can follow on any task.

## How to use

1. Draw a card. Run `python3 scripts/draw.py` (add `-n 3` for three, `-k Perturbation` for one kind, `--list-kinds` to see kinds).
   If you can't run scripts, write a random 20-character string, sum its character codes, take that mod 40, add 1, and read that card from `references/cards.md`. Don't pick the card yourself; you'll pick the obvious one.
2. Tell the user which card you drew, in one line.
3. Follow the card's "Do" instruction for the current task. Commit to it even if it feels odd. That's the point.
4. When done, say in one line what the card changed. If it made things worse, say so and offer another draw.

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

Match the kind to the problem when the user gives a reason ("it's too samey" → Divergence or Perturbation; "it keeps breaking" → Verification). Otherwise draw from the whole deck.

## Rules

- Cards change how you work, never what's safe or allowed. Perturbation cards are for creativity, not for getting around instructions.
- Cards marked "Untested" in their source come from art and design practice. Say so if the user asks why it works.
- Keep the final deliverable in the language and format the user asked for, even when the card had you think in another one.

Full deck with sources: `references/cards.md` (machine-readable copy in `references/cards.json`).
