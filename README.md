# skills

## Our own skills

| Skill | What it does |
|---|---|
| [`site-teardown`](skills/site-teardown/SKILL.md) | Turn a live website into a measured teardown: geometry per breakpoint, motion values, components, creative direction, conversion. Extract reusable styles, tricks and components into the design-kit, then grade the teardown with a blind rebuild. Scripts: capture, fetch-source, compare, record + side-by-side video |
| [`design-kit`](skills/design-kit/SKILL.md) | Shortlist and apply styles, tricks and components from the private `milesarthursmith/design-kit` repo to a project |
| [`name-hunt`](skills/name-hunt/SKILL.md) | Find a name for a company or product with the founders in the loop: competitor naming scan, parallel generator subagents per style, .com/.com.au registry checks, a swipe-deck artifact founders vote in, live-call pass, deep-dive on the favourite, trademark pre-check, write-up. Builds on [hunainx/startup-naming](https://github.com/hunainx/startup-naming) (MIT) |
| [`oblique-strategies`](skills/oblique-strategies/SKILL.md) | Draw random cards and send one subagent per card to bring back unusual ideas, so the main session stays clean. 40 cards reverse-engineered from AI advances (verbalized sampling, AlphaEvolve, Karpathy's autoresearch loop, Reflexion, agent memory) plus perturbations (think in another language, encode the plan, ban a letter). Script: draw by kind |
| [`mine-claude`](skills/mine-claude/SKILL.md) | For developers: pull every correction and complaint you gave Claude Code from your transcripts (local, on the web, history.jsonl), with what Claude was doing, the error and an exact quote checked against the source. AI clusters the feedback into the failure modes that repeat, with no preset categories, and turns them into rules for `.coderabbit.yaml` review instructions, CLAUDE.md, hooks, coding-agent prompts or evals. Scripts: collect, batch, extract, merge, quote check, two-pass clustering, usage counts, combine two machines. Web download builds on [simonw/claude-code-transcripts](https://github.com/simonw/claude-code-transcripts) (PR #93) |

Install into a project: `npx skills add milesarthursmith/skills` (or copy `skills/<name>/` into the project's `.claude/skills/`).

## Forked third-party skills

Forked copies of GTM / marketing Claude Code skill repos, tracked as git submodules so each keeps its own history and can be pulled to latest independently.

| Submodule | Source | Author |
|---|---|---|
| `marketingskills` | [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) | Corey Haines |
| `gtm-cofounder` | [AIDevGTM/gtm-cofounder](https://github.com/AIDevGTM/gtm-cofounder) | Shane O'Connor |
| `gtm-skills` | [Prospeda/gtm-skills](https://github.com/Prospeda/gtm-skills) | Prospeda |
| `claude-marketing` | [thatrebeccarae/claude-marketing](https://github.com/thatrebeccarae/claude-marketing) | Rebecca Rae Barton |
| `claude-gtm-plugin` | [manojbajaj95/claude-gtm-plugin](https://github.com/manojbajaj95/claude-gtm-plugin) | Manoj Bajaj |
| `devmarketing-skills` | [jonathimer/devmarketing-skills](https://github.com/jonathimer/devmarketing-skills) | Jonathan Reimer |
| `gtm-eng-skills` | [getaero-io/gtm-eng-skills](https://github.com/getaero-io/gtm-eng-skills) | Aero |
| `genesys-skills` | [matteotitta/genesys-skills](https://github.com/matteotitta/genesys-skills) | Matteo Tittarelli |

## Updating

```bash
git submodule update --remote --merge
```
