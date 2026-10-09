# skills

## Our own skills

| Skill | What it does |
|---|---|
| [`site-teardown`](skills/site-teardown/SKILL.md) | Turn a live website into a measured teardown: geometry per breakpoint, motion values, components, creative direction, conversion. Extract reusable styles, tricks and components into the design-kit, then grade the teardown with a blind rebuild. Scripts: capture, fetch-source, compare, record + side-by-side video |
| [`design-kit`](skills/design-kit/SKILL.md) | Shortlist and apply styles, tricks and components from the private `milesarthursmith/design-kit` repo to a project |

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
