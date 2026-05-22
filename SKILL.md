---
name: editease-design
description: Use this skill to generate well-branded interfaces and assets for EditEase, either for production or throwaway prototypes/mocks/etc. Contains essential design guidelines, colors, type, fonts, assets, and UI kit components for prototyping.
user-invocable: true
---

Read the README.md file within this skill, and explore the other available files.

If creating visual artifacts (slides, mocks, throwaway prototypes, etc), copy assets out and create static HTML files for the user to view. If working on production code, you can copy assets and read the rules here to become an expert in designing with this brand.

If the user invokes this skill without any other guidance, ask them what they want to build or design, ask some questions, and act as an expert designer who outputs HTML artifacts _or_ production code, depending on the need.

Key files:
- `README.md` — full system overview, content + visual + iconography rules
- `colors_and_type.css` — drop-in CSS variables (surfaces, text, status, spacing, radius, shadow, motion, type scale)
- `assets/` — `logo.svg`, `logo-mark.svg` (SVG wand icon mark from lucide)
- `preview/*.html` — canonical examples of every token, badge, button, card and brand surface
- `ui_kits/web_app/` — interactive recreation: Landing, Auth, Workspace (Dashboard / Review Queue / Uploads / Organized Videos)

Brand essentials:
- **Palette**: GitHub-Dark inspired. Surfaces `#0d1117` → `#161b22` → `#21262d`. Text `#c9d1d9` / `#8b949e` / `#6e7681`. Accent `#58a6ff` (blue). Status: success `#238636/#3fb950`, warning `#d29922`, danger `#da3633`. Marketing pair: accent + purple `#a371f7`.
- **Type**: Inter (UI) + JetBrains Mono (kickers / timecodes / labels). Display title uses `clamp(3rem, 6vw, 5.5rem)`, weight 700, tracking −0.03em.
- **Motion**: cinematic `cubic-bezier(0.16, 1, 0.3, 1)`. 0.55 s page enter, 0.95 s curtain lift, 35 s marquee.
- **Surfaces**: glass workspace panels (rgba 0.68 + 16 px blur, 24 px radius, 6 % white border). Bento dashboard cards w/ 2 px accent strip on top.
- **Iconography**: `lucide-react` (1.5–1.6 stroke). No emoji in product UI; sparingly in onboarding/tour copy. Status uses colored dot + label, never emoji.
- **Copy**: clear, kinetic, second person. Mono caps for kickers; sentence-case for headlines; never ALL CAPS in body copy.
