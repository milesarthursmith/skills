---
name: design-kit
description: Browse and apply the design-kit (styles, components, tricks) captured from great websites to a project. Use when building or restyling a site and someone says "use the kit", "try the <style> style", "add a trick like <site>'s", "what styles/tricks do we have", or wants design options for a project. Pairs with site-teardown, which fills the kit.
---

# Design kit: use it on a project

The kit lives in the private repo **`milesarthursmith/design-kit`** (clone it, or ask for it to be attached). Paths below are relative to it:
- `styles/<name>/`: a whole look (`DESIGN.md` + `tokens.css` + `demo.html`).
- `components/<name>/`: reusable UI pieces, skinned by CSS variables.
- `tricks/<name>/`: single techniques with drop-in code, knobs and a demo.
- `teardowns/<slug>/`: the evidence each one came from.
- `README.md` + `index.html`: the index and a visual gallery of everything (`?style=<name>` reskins demos).
- `styles/_contract.md`: the CSS variables every component and trick reads.

## To offer options
1. Read `README.md`'s index, then the project's brief and brand constraints (voice, colours, audience).
2. Shortlist 2–3 styles and 3–6 tricks that fit. For each, give one line on why it fits and what it would clash with. Link the `demo.html`.
3. If the user wants to see them, build quick variants. Apply `tokens.css`, swap in the components, and add the tricks. Keep the project's own content and brand colours unless asked otherwise.

## To apply a style
- Read its `DESIGN.md` fully. The **Anti-patterns** and **Applying it to a new project** sections matter most.
- Map the project's brand onto the style's token roles (`--accent`, `--surface`, …) rather than copying the source site's colours.
- Keep the source site's assets, logos and copy out of the project. The kit holds only our own reimplementations.

## To add a trick
- Copy the drop-in code, set the knobs, and keep the reduced-motion branch.
- Check its **When not to use** line against the project. A trick that fights the brand is a no.

## After using it
Note which kit items the project used (in the project's notes) so the kit's README can show "used on" and what worked.
