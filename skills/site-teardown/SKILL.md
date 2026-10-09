---
name: site-teardown
description: Deconstruct a live website into a measured teardown (creative direction, design system, layout geometry, motion with real values, components, patterns, conversion) and extract reusable components, tricks and a design style into the design-kit. Use when someone shares a URL and asks how it's built, wants its animations or design deconstructed, wants to "steal" a style, or wants inspiration sites turned into reusable parts. Includes a blind-rebuild quality gate that scores the teardown.
---

# Site teardown

Turn a reference site into **measured evidence**, then into **reusable parts** (components, tricks, a style) that other projects can use. The rule: **the browser and the site's own CSS/JS are the source of truth.** Never write a value you could have measured.

Why it's built this way: a first teardown done from reading code only got the hero/pricing shader mixed up, missed Rive, and inferred scroll timing. A later version measured motion live but left out layout geometry and timelines, so a blind rebuild scored B+ and had to guess every position. Each step below closes one of those gaps.

## Where the output goes
The kit is the private repo **`milesarthursmith/design-kit`** (clone it next to your project). `teardowns/`, `tricks/`, `components/`, `styles/`, their `_template`s, the token contract (`styles/_contract.md`), `KIT-PLAN.md` and `README.md` all live there. Paths below are relative to that repo. `scripts/` is relative to this skill.

## 0. Setup (2 min)
- Need Node + Playwright with Chromium. `scripts/capture.mjs` imports Playwright from `/opt/node-tools/node_modules/playwright` (Claude Code cloud) and falls back to `npm i playwright`.
- **Chrome DevTools MCP does not work in cloud containers** (no Chrome binary, runs as root). Use Playwright.
- Headless Chromium has **no H.264**, so MP4 videos won't play. Anything that depends on playback (focus modes, "on video end") must be read from source and marked NOT OBSERVED.
- **Locale crash:** cloud containers report `en-US@posix`, which crashes Intl-heavy React sites (Railway rendered with no animations). The scripts force `locale:'en-US'`. If `geometry.json` lists page errors, read them before trusting the capture.
- **Inner-scroll sites** (app-like desktops such as PostHog, and Lenis/locomotive wrappers): if `geometry.json` shows the page height equal to the viewport, the page scrolls inside a container. Page-scroll shots will be empty. Find the `overflow:auto|scroll` element and drive it (and any windows) by hand in step 3.
- **One-way scroll triggers** (e.g. Collins' theme flip at the middle of the screen): the capture jumps between positions, so one-off triggers can fire out of order and leave later shots in the wrong state. Confirm any state change by scrolling with `page.mouse.wheel` from the top.
- **Scroll-hijack slideshows** (e.g. MetaLab): every section sits at top 0 with full-screen height, and wheel events switch slides. The capture can't step through them. Drive them with `page.mouse.wheel` and screenshot each slide.
- **Div-only builders** (Framer, Webflow, Wix): sections are `div`s. The capture falls back to the tall full-width children of the main wrapper. Check `geometry.json` has more than 3 sections.
- Respect the site: public pages only, no logins, no bypassing walls. Study use; don't ship their assets or copy.

## 1. Check what you already have
- Look in `teardowns/` for an existing teardown of this site, and in `tricks/`, `components/` and `styles/` for patterns you've already captured. Extend, don't redo.
- Check the project's own notes for why this site matters (founder comments, briefs). Write the "why we're studying it" line first. It steers what to go deep on.

## 2. Capture: one command
```bash
node scripts/capture.mjs <url> <workdir>/<slug>          # 4 breakpoints: 1440, 1024, 834, 390
node scripts/capture.mjs <url> <workdir>/<slug> --quick  # desktop only, for quick passes
```
Writes geometry per breakpoint, media queries, keyframes, load-in animation timings, a class/style mutation timeline, scroll-linked transforms, components with screenshots, hovers, WebGL shader sources and uniforms, SVG filters, tokens, copy, meta, network, reduced-motion check, viewport shots, full-page shots and scroll videos. The file list is in the script header.

Then pull the source, which is the referee for every disputed value:
```bash
bash scripts/fetch-source.sh <url> <workdir>/<slug>/src   # HTML + every CSS/JS file in network.json
```
`stack.json` only sees libraries exposed as page globals. Bundled modules (GSAP, Lenis, Motion) won't show there, so **confirm the stack by grepping the source** (`grep -l 'ScrollTrigger\|lenis\|framer-motion\|motion-dom' src/*`). Grep it for the motion maths: `cubic-bezier`, `@keyframes`, `stiffness|damping|mass`, `IntersectionObserver` + `rootMargin`, `requestAnimationFrame`, `matchMedia`, `prefers-reduced-motion`, `uniform`, `ScrollTrigger|lenis|gsap`.

## 3. Interactions the script can't guess
Drive these by hand with Playwright, and screenshot each state: toggles/tabs, accordions, modals, drag, video players, menus at mobile size, forms (empty/error/success), any "play" or "try it" moment. Record start → end states and timing. For drag: sample position every 30ms after release (momentum or a dead stop?).

## 4. Analyse: four lenses, in parallel if you can spawn agents
Give every agent the same capture folder and these rules: cite the measured value or the source line, mark guesses INFERRED, and don't contradict the CSS.

| Lens | Method (use the external skill if installed, otherwise the core questions) |
|---|---|
| **Creative direction + identity** | rampstack `creative-direction` axes (tone register, aesthetic philosophy, audience relationship, sensory ambition, plus what it rules out). `brandbook-skill` design model: observed vs derived, falsifiable anti-patterns, fit check (system vs crafted assets) |
| **Motion** | Emil Kowalski `review-animations` + `apple-design`: easing, duration, properties, origin, interruptibility, frequency, springs (calculate the damping ratio), reduced motion. Name every pattern in `animation-vocabulary` terms |
| **Critique + patterns** | Awwwards rubric (Design 40, Usability 30, Creativity 20, Content 10). Impeccable heuristics plus cognitive load. Measured contrast and tap targets. Then a **pattern catalogue**: name, where, how (values), why it works, when to steal |
| **Conversion + voice** | page-cro: value prop, headline, CTAs per device, narrative order, proof, objections, friction, pricing. Voice with real quotes |

## 5. Write the teardown: `teardowns/<slug>/teardown.md`
Use `teardowns/_template.md`. **Required sections.** The blind-rebuild test failed on each one that was missing:
1. **Geometry table per breakpoint:** each section's top and height, container/content width, sticky elements, plus key element boxes for the hero and repeated components. Copy from `geometry.json`.
2. **Exact breakpoint conditions:** quote the real media queries (e.g. `(max-width:1023px) and (hover:none) and (pointer:coarse)`), never "on mobile".
3. **Tokens:** colour roles, type scale with tracking and weights (including the exceptions), radii mapped to components, shadows mapped to components.
4. **Motion table:** every animation with trigger, properties, duration, delay, easing or spring constants, and whether it replays. Formulas verbatim for scroll-linked motion.
5. **Timelines for scripted sequences:** step / start ms / duration / what changes (load-in order, typing speed, loop keyframe percentages).
6. **Component inventory:** each repeated component with dimensions, internals, all states (hover/active/open/disabled) and a screenshot reference.
7. **Effect parameters:** shader constants and palette, SVG filter markup, Rive/Lottie files, canvas resolution scaling.
8. **Creative direction, critique, conversion:** the four lens summaries.
9. **Not observed:** an explicit list.
10. **Mobile internals and full copy:** padding and gaps per section at 390 (not just heights), and every text block, including accordion bodies and all testimonials.
11. **One source of truth:** resolve every conflict between lens files before you finish, with the CSS as referee.

## 6. Extract to the kit (this is the reusable payoff)
- **Tricks** (`tricks/<name>.md`, using `tricks/_template.md`): one self-contained technique with a working snippet and its knobs. Example: spring-lagged marquee, glass that downgrades while scrolling, device-aware CTA. Rewrite it in your own code; don't paste minified source.
- **Components** (`components/<name>/`, using `components/_template/`): `README.md` spec (anatomy, dimensions, states, tokens it uses) plus `component.html` and a standalone demo.
- **Style** (`styles/<name>/`, using `styles/_template/`): `DESIGN.md` (sections: visual theme, colour, typography, spacing, layout, components, motion, voice, anti-patterns) plus `tokens.css` and `demo.html`. Name styles by look, not by site (e.g. `retro-desktop`). Record the source site inside.
- Add each new item to the kit, then run `python3 scripts/build-index.py` in the design-kit repo to regenerate its README index and `index.html` gallery.

## 7. Quality gate: blind rebuild (do not skip)
To see motion side by side: `node scripts/record.mjs <url> <out.webm> '<steps json>'` on the original and the rebuild (same steps, so the clips stay in sync), then `bash scripts/sbs.sh left.webm right.webm out.mp4 "original" "rebuild"`.

1. Spawn an agent that may read **only** the teardown and the kit items, and never the live site or source. It rebuilds the page with placeholder assets and logs every gap in `GAPS.md`.
2. Run `node scripts/compare.mjs <original-url> <out>/original` and the same on the rebuild. Compare page and section heights, the headline, fonts, colours, hovers, scroll-linked curves and reduced motion. Make side-by-side sheets.
3. Grade by area (tokens, motion, layout, mobile, choreography, uncaptured components) and overall. Fix every teardown error the test exposes, then record the grade in the teardown. Reference result: heyclicky went from B+ (v1, no geometry or timelines) to A- (v2, all required sections), with desktop section heights going from 7.9% off to exact.
The grade is the honest measure of the teardown. A teardown that hasn't been rebuilt is a draft.

## Output
`teardowns/<slug>/` (teardown.md, SCORECARD.md, small evidence files and a few key screenshots; keep videos out of git), plus new `tricks/`, `components/` and `styles/` entries and updated README index rows.
