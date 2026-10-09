---
name: design-kit
description: Try out components, motion tricks and design styles from the design-kit (studied from 20 great websites) inside a real website, see before vs after, then keep or revert. Use when building, restyling or polishing a site and someone says "try the kit", "what would make this hero better", "add a reveal like relace", "make it feel like <site>", "give me options for this section", or "use our inspiration". Pairs with site-teardown, which fills the kit.
---

# Design kit: try it on a real site

**The goal:** take inspiration from sites we've studied and **try it on the site you're working on**. You find a candidate, drop it into one section on a branch, look at it next to the original, and keep it or bin it. Small, reversible experiments, not a redesign.

The kit is the private repo **`milesarthursmith/design-kit`** (attach or clone it beside the project). What's in it:
- **`catalog.json` / `CATALOG.md`:** every pattern we've seen, indexed by **job** (hero, proof, pricing…) and **feel** (warm, playful, editorial…), with a status:
  - `built`: drop-in code exists.
  - `planned`: spec with real values is in `KIT-PLAN.md`.
  - `seen`: values are in a teardown.
- **Built items:** `styles/` (whole looks: `DESIGN.md` + `tokens.css`), `components/`, `tricks/`, each with a README and a `demo.html`.
- **Supporting files:** `styles/_contract.md` (the CSS variables every item reads), `teardowns/` (the evidence), `compare/` (source vs kit videos), and `index.html` (visual gallery).
- **`projects/<site>/`:** per-site memory. `PROFILE.md` holds the brand direction, the token mapping, the motion the site already has, gotchas and a **try-on log**. It also holds a ready-made `kit-tokens.css`.
- Our own reimplementations only. Never ship a source site's assets, logos or copy.

## The try-on loop

### 0. Load the project profile
Read `projects/<site>/PROFILE.md` in the kit. It tells you what was already tried, the safe token mapping and the traps. If there's no profile, create one from `projects/humanstuff-website/PROFILE.md` as a template before you start. The next agent depends on it.

### 1. Frame the job (2 minutes, before looking at the kit)
Write down three things:
- the **section** you're improving
- the **job** it has to do, using the catalogue's job words (e.g. "hero: show the product working")
- the **feel** wanted, as 2–3 feel words from the project's brand or brief

If the brief names reference sites ("like relace"), look up their `kind: site` entries in `catalog.json` for the axes and best parts. Read the project's brand rules first (voice, colours, must-nots). For humanstuff.ai that's `departments/marketing/voice.md` and the founders' design guidance.

### 2. Find 2–3 candidates
Run `python3 scripts/find.py --job <job> --feel <a,b>` in the kit (`--site relace` shows a site's axes and best parts). It ranks built items first. Then:
- **First, grep the project for a home-grown version** (e.g. a `.reveal` class, a shape field, a marquee). Replacing that with the kit item, site-wide, is often the better try-on: it usually gains reduced-motion support and pause controls.
- Prefer `built` items. They try on in minutes.
- Check each candidate's `when_not` against the project.
- Watch its `compare/` video if there is one, so you know how close the kit version is to the source.
- Offer the user the candidates in one line each: what it does for the visitor, its effort, and a preview link.
- If nothing fits, say so. Don't force a pattern.

### 3. Map tokens once per project (scoped, never `:root`)
Kit items only read the contract variables (`--bg`, `--ink`, `--accent`, `--accent-text`, `--font-display`, `--ease-out`, `--dur-*`, …).
- If the profile has a `kit-tokens.css`, copy it to the project's `src/kit/`.
- Otherwise write one:
  - Put the brand mapping on a **wrapper class**: `.kit-scope { --accent: var(--brand-blue); … }`.
  - Add a `.kit-dark` override for dark sections.
  - Start from `styles/_base/defaults.css` for the non-colour values.
- **Never on `:root`:** frameworks own those names. shadcn's `--accent` is a bare HSL triplet, and overwriting it breaks every `bg-accent`.
- Find the site's real colour source before mapping. On the humanstuff site it's `src/styles/hs.css`, not shadcn.
- Check contrast per scope (text ≥ 4.5:1). Brand colours often fail as `--accent-text`. A colour can pass on light and fail on dark: humanstuff's orange is 3.1:1 on the page but 5.7:1 on night.
- Don't import a kit style unless you're deliberately trying that style.
- Record the mapping and its ratios in the profile.

### 4. Drop it in (one section, on a branch)
Make a branch named `try/<item>-<section>`. Copy the item's files into the project at `src/kit/<item>/`, starting each with a comment saying it's a kit copy and fixes go upstream in design-kit. Don't link the kit repo at runtime. Then follow the README's **Use** and **Use in React** sections.
- Add `class="kit-scope"` (plus `kit-dark` if needed) to the section.
- **Remove any home-grown motion on the same elements** (`.reveal` classes, `transitionDelay` props), or the effect runs twice.
- **Sticky items:** an ancestor with `overflow: hidden` silently breaks `position: sticky`. Switch it to `overflow: clip`.
- **Plain HTML:** add the markup or `data-*` attributes, link `trick.css`, and `import { init… } from './trick.js'`.
- **React:** put the CSS in the global stylesheet (or a module). Call the init in an effect and clean up:
  ```tsx
  useEffect(() => { const ctl = initSequencedReveal({ root: ref.current }); return () => ctl?.destroy?.(); }, []);
  ```
  Use `data-*` attributes and `className` as the README shows. If an item has no `destroy`, add a guard so it inits once.
- **Components:** port `component.html` markup to JSX (`class` → `className`) and keep the scoped CSS as is.
- Keep the item's reduced-motion branch and pause controls. They're part of the item, not optional.

### 5. Look at it: before vs after
Record the section on `main` and on the branch with the same steps, then stack them:
```bash
node <site-teardown>/scripts/record.mjs http://localhost:PORT/ before.webm '[{"scroll":Y,"ms":2000},{"wait":2000}]'
node <site-teardown>/scripts/record.mjs http://localhost:PORT/ after.webm  '<same steps>'
bash <site-teardown>/scripts/sbs.sh before.webm after.webm try.mp4 "before" "after - <item>"
```
Recorder options:
- `{"scrollTo":".how","offset":-80,"ms":2000}` scrolls to a section rather than a fixed Y, so clips stay aligned when the try-on changes section height.
- `RM=1 node record.mjs …` records with reduced motion.

Then run `node <site-teardown>/scripts/check.mjs http://localhost:PORT/ ".how"`. It checks console errors, horizontal overflow at 1440 and 390, and infinite animations under reduced motion, and screenshots the section at each width. Make sure the project still builds.

Show the user the video plus one honest line on whether it earns its place.

### 6. Keep or revert
- **Always append a row to the profile's try-on log:** date, section, item, verdict, video path and a one-line reason. Reverts teach the next agent as much as keeps do.
- **Keep:** merge the branch, or hand it to the founder to merge.
- **Revert:** delete the branch.
- **Feed back to the kit:** if a `planned` or `seen` pattern got built during a try-on, or you fixed a kit item, add it back to the kit using `site-teardown` step 6. Then rerun `python3 scripts/build-index.py` and `python3 scripts/build-catalog.py` in the design-kit repo.

## Rules of thumb
- **One new motion idea per section, two at most per page view.** Replacing an existing motion beats stacking one on top. Stacking tricks is how sites become "overstim" (founder feedback on relace).
- **Tokens before tricks.** A good palette and type scale fix more than any animation.
- **The `seen` and `planned` entries are inspiration with real numbers.** Build them small, in the project, then contribute them back.
