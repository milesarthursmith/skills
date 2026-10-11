# Card deck

Each card: the line, where it comes from, why it works, and the instruction to follow. Cards whose source starts with "Untested" come from art and design practice, not AI research.

## Divergence

### 1. Ask for five, with the odds.
- Source: Verbalized Sampling (2025)
- Why: Ask for one answer and you get the most typical one. Ask for a spread with probabilities and the model reaches into options it would normally suppress.
- Do: Before answering, list 5 genuinely different approaches and the rough probability you'd normally pick each. Then build the lowest-probability one that still meets the brief.

### 2. Roll the dice before you choose.
- Source: String Seed of Thought (Sakana AI)
- Why: Models are bad at being random. Making them write a random string first, then derive the choice from it, breaks the habit of picking the same option.
- Do: Write a random 20-character string. Use it (sum of character codes mod N) to pick which of the N options below you take. Commit to that option and do it well.

### 3. Remove the tool you'd reach for first.
- Source: Dropout
- Why: Randomly switching off parts during training stops a network leaning on one path. Taking away the default forces a different route.
- Do: Name the library, pattern or assumption you'd normally use here. You can't use it. Solve the task without it.

### 4. Branch before you commit.
- Source: Tree of Thoughts
- Why: Explore several partial solutions a few steps deep, then prune, instead of following the first line of thought to the end.
- Do: Sketch three different solutions two steps deep. Say which is weakest and why. Drop it and take the other two one step further before choosing.

## Effort

### 5. Think longer, not bigger.
- Source: Reasoning models / test-time compute
- Why: Spending more effort at answer time beat building a bigger model. The time goes in before the output, not after.
- Do: Before writing anything, spend a full pass on the problem: what's actually being asked, what's ambiguous, and three ways a first attempt would go wrong.

### 6. Write the steps before the answer.
- Source: Chain of thought
- Why: Models get more right when they lay out intermediate steps instead of jumping to a conclusion.
- Do: Write the steps you'll take as a numbered plan. Only then start, and tick each step off as you go.

### 7. Guess fast, check slow.
- Source: Speculative decoding
- Why: A small model drafts, a big model accepts or fixes. Most of the draft survives, so it's much faster.
- Do: Write a rough version end to end in one quick pass. Then go back slowly through each part and accept, fix or replace it.

## Verification

### 8. Who checks the work?
- Source: Self-verification / verifiers
- Why: Errors compound over many steps. A check the agent can't fake stops them stacking up.
- Do: Write the test or check that proves this works before you build it. You can't say it's done until that check passes.

### 9. One file, one number, one clock.
- Source: Karpathy autoresearch (2026)
- Why: An agent edits one file, optimises one metric, runs each try for a fixed time, keeps what improves and reverts the rest. It ran ~700 experiments in two days.
- Do: Pick one metric for this task. Change one thing, run it, measure. Keep the change only if the number improves; otherwise revert. Repeat 10 times and report the log.

### 10. Raise autonomy as the checks prove out.
- Source: The Karpathy loop
- Why: Freedom is earned. Start supervised, loosen as the verifier keeps passing.
- Do: Ask before each change until your checks have passed three times in a row. After that, carry on without asking and only stop for a failure.

### 11. Solve it three ways.
- Source: Self-consistency
- Why: Sample several independent answers and take the one they agree on. Disagreement is a signal.
- Do: Solve this three separate ways without looking at the earlier attempts. If they agree, ship it. If not, explain the disagreement before choosing.

## Critique

### 12. Write the rules, not the answers.
- Source: Constitutional AI
- Why: Instead of labelling every output, write principles and have the model judge itself against them.
- Do: Before starting, write 5 principles a good result must obey. When done, score the result against each principle and fix anything that fails.

### 13. Argue with yourself.
- Source: Debate / LLM-as-judge
- Why: A second voice whose only job is to find faults catches what the author misses.
- Do: Draft it. Then switch to a hostile reviewer who wants this rejected and list every weakness. Then switch back and revise.

### 14. Build it, then attack it.
- Source: AlphaZero self-play
- Why: Playing against yourself creates an opponent that's always exactly your level, so you keep improving.
- Do: Build it. Then try to break it as an adversary: bad inputs, edge cases, misuse. Fix what breaks. Do one more round.

## Search

### 15. Breed, don't design.
- Source: AlphaEvolve (DeepMind)
- Why: An LLM proposes code changes, an evaluator scores them, the best survive and get mutated again. It found algorithms people hadn't in decades.
- Do: Produce 4 variants. Score each against the criteria. Keep the best 2, combine their strongest parts into a new variant, change one thing. Run 3 rounds.

### 16. Keep the best of each kind.
- Source: MAP-Elites (inside AlphaEvolve)
- Why: Keep a winner per niche, not one overall winner, so good-but-different ideas survive to be used later.
- Do: Keep a shortlist with a slot each for: simplest, fastest, cheapest, most unusual. A new idea only replaces the one in its own slot.

### 17. Act, look, then think.
- Source: ReAct
- Why: Interleave small actions with reading the results, instead of planning everything up front.
- Do: Take the smallest action that will tell you something new. Read the result. Only then decide the next action.

## Memory

### 18. Keep notes for your next self.
- Source: Agent memory / persistent state files
- Why: Agents forget between sessions. A file of what was tried and what's next lets work carry on.
- Do: Keep a NOTES.md with: what you tried, what failed and why, what's next. Read it before every step and update it after.

### 19. Write down the lesson after you fail.
- Source: Reflexion
- Why: After a failure, the agent writes a short reflection and reads it before retrying. It learns without retraining.
- Do: After each failed attempt, write one sentence on why it failed and one rule to avoid it. Read all the rules before trying again.

### 20. Do it twice, save it once.
- Source: Voyager skill library / Agent Skills
- Why: Successful procedures get saved with a name and a 'when to use' line, then reused instead of rediscovered.
- Do: If you do something more than once, save it as a named procedure with one line on when to use it. Check your saved procedures before starting new work.

## Context

### 21. Load only what this step needs.
- Source: Progressive disclosure (Agent Skills)
- Why: Agents see a one-line summary of each skill and open the full instructions only when needed, so the context stays clean.
- Do: Start with a one-line summary of each source or file. Open the full content only when the current step needs it.

### 22. Give it a clean desk.
- Source: Sub-agents / context isolation
- Why: A fresh agent with only the brief does a side task, then hands back the conclusion, not its mess.
- Do: Hand this sub-question to a fresh agent with only the brief. Take back its conclusion in five lines or fewer, not its working.

### 23. Look it up, don't remember it.
- Source: RAG / tool use
- Why: Models answer better about the world when they fetch the facts instead of recalling them.
- Do: Treat every fact about the current world as unknown until you've fetched a source. Note the source next to each claim.

## Structure

### 24. Many specialists, one router.
- Source: Mixture of experts
- Why: Only the relevant experts handle each input, so the system is big but each step is cheap and focused.
- Do: Split the problem into parts by type. For each part, name the expert who'd handle it best and answer that part as them.

### 25. Agree on the plug, not the appliance.
- Source: MCP / agent interoperability
- Why: A shared protocol let any tool talk to any agent. Fix the interface and the parts become swappable.
- Do: Define the interface between parts first (inputs, outputs, errors). Build each part so it only talks through that interface.

### 26. Change only a little.
- Source: LoRA
- Why: Adapt a huge model by training a tiny add-on and leaving the rest frozen.
- Do: Find the smallest change that gets the result. Leave everything else exactly as it is, and list what you didn't touch.

### 27. Do it the slow way once, then write the shortcut.
- Source: Distillation
- Why: A big model's outputs train a small one that does most of the job for a fraction of the cost.
- Do: Solve this the thorough way once. Then write the simple rule or script that would get 90% of the way next time.

### 28. Change the reward, not the worker.
- Source: RLHF / RL post-training
- Why: Most recent gains came from changing what models are rewarded for, not their size.
- Do: Before working, write down what 'good' means here as a score you could give. Optimise for that score, not for looking finished.

## Perturbation

### 29. Think in a language far from English.
- Source: Language of Thought study (2026)
- Why: Making a model reason in another language and answer in English raised output diversity. Languages further from English helped more, and mixing languages helped again, at a small cost in quality.
- Do: Do all your thinking in Tagalog (or Hebrew, or Occitan). Write only the final answer in English.

### 30. Ask in five languages, then merge.
- Source: Multilingual prompting (2025)
- Why: Rewriting a prompt in several languages with local cultural framing, answering each, then combining, beat high temperature and persona prompts for diversity.
- Do: Rewrite this brief in Japanese, Swahili, Portuguese and Finnish, each with a framing a local would use. Answer each version separately. Then merge the best ideas into one English answer.

### 31. Start from a word that doesn't belong.
- Source: Random concept infusion (2026)
- Why: Putting a random word or sentence in front of a prompt increased unique answers across four models. The effect was real but small, so use it as a nudge.
- Do: Unrelated word: [PASTE RANDOM WORD]. Before starting, write two sentences on how this word could change the solution. Then let it shape at least one decision.

### 32. Write the plan in Morse.
- Source: Untested · encoding as a speed bump
- Why: Forcing a plan through an awkward encoding slows the model down and breaks its stock phrasing. Not tested in research; try it and compare.
- Do: Write your plan in Morse code (or as a recipe, a chess game, or a regex). Then decode it back into plain English and build what the decoded version says, not what you first meant.

### 33. Explain it without the letter e.
- Source: Untested · Oulipo constraints
- Why: Writers used arbitrary rules to escape their habits. An agent can't fall back on its usual words when they're banned.
- Do: Describe your approach without using the letter e. Then describe it again in plain English and note anything that changed.

### 34. Misread the brief on purpose.
- Source: Untested · deliberate misinterpretation
- Why: The 'wrong' reading often exposes an assumption the right reading hid.
- Do: List 3 ways this brief could be misread. Sketch the most interesting misreading. Say what it reveals about the real brief, then do the real one.

### 35. It's a plumbing problem.
- Source: Untested · Synectics / analogy transfer
- Why: Describing a problem in another field's terms imports that field's fixes.
- Do: Re-describe this problem as if it were a problem in plumbing (or beekeeping, or air traffic control). How would that trade solve it? Translate the answer back.

### 36. It was built in 1987.
- Source: Untested · time-shift
- Why: Older constraints (no cloud, tiny memory, paper forms) push toward simpler designs.
- Do: Pretend this had to be built in 1987 with that era's tools. Describe that version. Keep anything from it that would still make ours simpler.

### 37. Design the worst version, then flip it.
- Source: Untested · reverse brainstorming
- Why: Bad ideas are easier to generate, and their opposites are often less obvious than the first good idea.
- Do: Design the worst possible version of this in 8 bullet points. Then invert each bullet and build from the inverted list.

### 38. Make it a different object.
- Source: Untested · form forcing
- Why: Forcing the output into a foreign format (a board game's rules, a song's structure, a tax form) changes how it gets organised.
- Do: Write the solution as the rules sheet for a board game. Then convert the rules back into a spec.

### 39. The user isn't human.
- Source: Untested · perspective shift
- Why: Designing for an odd user surfaces assumptions about who it's for.
- Do: Describe how this would work if the user were a cat, a robot, or someone who only has 10 seconds. Keep one idea from each that improves it for real users.

### 40. Answer as two people who disagree.
- Source: Untested · split persona
- Why: Two named voices with opposite instincts produce a wider spread than one voice asked to be balanced.
- Do: Answer twice: once as a cautious engineer, once as a reckless artist. Then write a third answer that steals the best part of each.
