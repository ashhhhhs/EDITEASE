# EditEase Design System

EditEase is an **AI-powered video editing platform** for post-production teams. It ingests raw footage, runs scene detection + emotion analysis, and gives reviewers a visual clip-grid workspace with role-aware controls (admin / reviewer / editor). The platform's tagline is "Stop sorting footage manually."

This design system distills the live frontend (React + Vite, GitHub-Dark inspired palette) into reusable tokens, components, and UI kits so future product work stays visually consistent — without changing the existing colour palette.

## Sources

- **Codebase** — [`ashhhhhs/EDITEASE`](https://github.com/ashhhhhs/EDITEASE) (`frontend/` directory).
  Key files imported:
  - `frontend/src/index.css` — base tokens + components
  - `frontend/src/landing.css` — marketing landing styles
  - `frontend/src/auth.css` — auth shell
  - `frontend/src/Landing.jsx`, `AppShell.jsx`, `Dashboard.jsx`, `Login.jsx` — reference screens
  - `frontend/src/components/*` — shared primitives (`PageHeader`, `EmptyState`, `AuthShell`)
- **Stack** — React 19 · Vite · React Router · GSAP + Lenis (scroll/animation) · Recharts · Lucide React (icons) · react-joyride (tours)

## Index

```
README.md                  ← you are here
SKILL.md                   ← skill manifest (also usable in Claude Code)
colors_and_type.css        ← all design tokens (colours, type, spacing, motion)

assets/
  logo.svg                 ← EditEase wordmark + glyph
  logo-mark.svg            ← square glyph only
  vite.svg                 ← legacy favicon (current production)

preview/                   ← cards rendered in the Design System tab
  colors-surfaces.html
  colors-text.html
  colors-status.html
  colors-accent-purple.html
  type-display.html
  type-headings.html
  type-body-mono.html
  spacing-scale.html
  radius-shadow.html
  motion-easing.html
  components-buttons.html
  components-badges.html
  components-inputs.html
  components-cards.html
  components-stat.html
  components-clip.html
  components-nav.html
  components-empty-state.html
  brand-logo.html
  brand-glow-atmosphere.html

ui_kits/
  marketing/               ← public landing page recreation
    index.html, README.md
  workspace/               ← authenticated app shell + dashboard
    index.html, README.md
```

## Content Fundamentals

**Voice:** confident, subtractive, builder-y. EditEase positions itself as removing tedium ("Stop sorting footage manually") and uses crisp imperatives over fluff. Sentences are short, sometimes one word ("Upload. Analyze. Review. Download.").

**Person:** *we* / *you* split — the product speaks of itself in third person ("EditEase detects every scene") and addresses users as *you* ("Drop in your raw files. We'll split the scenes…"). First-person plural ("we") is used in dashboard banners ("We've sent a verification link").

**Casing:**
- **Sentence case** for headings, button labels, nav items ("Get Started", "Open Workspace", "Review Queue", "Organized Videos")
- **UPPERCASE + tracking** for mono kickers and badges ("APPROVED", "PENDING", "FLAGGED", "SCENE DETECTION · BATCH REVIEW")
- **Title Case** rare — only on proper nouns or section labels in the sidebar ("Workspace", "System")

**Tone examples:**
- Hero: *"Stop sorting footage manually. Upload your videos. EditEase detects every scene, analyzes emotion, and gives you a review workspace in minutes."*
- Empty state: *"No footage yet — Upload your first video and let the AI organise it into categories automatically."*
- Verification banner: *"Please verify your email address to unlock all features."*
- Section descriptions are technical and concrete: *"Distribution of raw clips by human review state."*

**Vibe:** cinema-meets-CLI. Editorial display type sits next to mono kickers and traffic-light dots. The product feels like a piece of professional kit, not a SaaS.

**Emoji usage:** rare and never in production UI copy. Only present in the **react-joyride onboarding tour** as visual hooks (🎬 📊 ⬆️ 🔍 ✨ ⚡ 📍 🎯) and one empty-state ornament (📂). Not part of the brand.

**Iconography over emoji:** Lucide icons are the standard for everything else.

## Visual Foundations

**Aesthetic:** GitHub-Dark base (`#0d1117`) + cinematic glass + editorial type. The system feels engineered (mono labels, scanlines, traffic-light dots) but never sterile (atmosphere blobs, scroll-driven curtain, particle canvas in the hero).

**Colour vibe:** cool dominant blue (`#58a6ff` accent) with a warm-purple secondary (`#a371f7`) used **only** in marketing gradients. Status colours (success green, warning amber, danger red) are GitHub-Primer derived and used consistently across review states (APPROVED / PENDING / FLAGGED).

**Type:**
- **Inter** for everything UI — weights 300, 400, 500, 600, 700
- **JetBrains Mono** for kickers, timecodes, badge labels — weights 400, 500
- Editorial display sizes use `clamp()` for responsive scaling (`clamp(3.5rem, 8.5vw, 7.6rem)` on the hero)
- Tracking is aggressive on the display end (`-0.05em` on hero, `-0.03em` on display title) and loose on mono kickers (`0.12em`).

**Spacing:** strict 4-px grid, exposed as `--space-4` through `--space-64`. No half-pixels, no ad-hoc margins.

**Backgrounds:** layered radial gradients on the marketing page —
```
radial-gradient(circle at top left,  rgba(88,166,255,0.12), transparent 26%),
radial-gradient(circle at 78% 16%,  rgba(163,113,247,0.12), transparent 22%),
linear-gradient(180deg, #0d1117 0%, #0b1017 100%)
```
plus blurred 90-px **atmosphere** orbs (`.landing-atmosphere`, `.workspace-ambient`) and a faint grid overlay masked by a center-out radial. **A noise grain SVG (`opacity: 0.025`) sits over everything** to kill banding. No full-bleed photos, no illustrations, no hand-drawn art.

**Animations:** scroll-driven and cinematic.
- Easing is almost always `cubic-bezier(0.16, 1, 0.3, 1)` (the "expo.out" / cinematic curve)
- Page enters with a 0.55 s `pageEnter` (12 px lift + fade)
- Hero H1 uses **SplitType** for per-character 3-D tumble (`yPercent: 110, rotateX: -40`)
- A **landing curtain** lifts off `yPercent: -110` in 0.95 s on mount
- Stat cards lift `-3 px` on hover; clip thumbs scale `1.04` over `0.5 s`
- Marquee runs 35 s linear; reduced-motion users get all animations disabled
- No bounces. No spring-back except on the magnetic nav CTA (`elastic.out(1,0.5)` GSAP).

**Hover states:** opacity drop (`0.94` on primary CTA), border colour darken to `var(--border-default)` or accent, subtle `var(--hover-surface)` (`rgba(255,255,255,0.05)`) overlay on nav items. Stat/bento cards add a coloured `0 0 32px ${accent}22` glow.

**Press / active states:** `var(--pressed-surface)` (`rgba(255,255,255,0.10)`). Active nav items get a left-to-right gradient (`linear-gradient(90deg, rgba(88,166,255,0.14), rgba(88,166,255,0.04))`) with an accent border.

**Borders:** 1 px solid; default `--border-subtle` (`#30363d`), hover `--border-default` (`#484f58`). Glass surfaces use `rgba(255,255,255,0.06)` for an even softer edge.

**Shadows:** four-tier scale —
- `--shadow-card` (4 px / 12 px) — resting cards
- `--shadow-hover` (8 px / 24 px) — hover state
- `--shadow-modal` (16 px / 48 px) — modals + popovers
- Marketing-only deep shadow `0 40px 120px rgba(0,0,0,0.46)` on the hero device

**Glass / blur:** `backdrop-filter: blur(16px)` (panels) and `blur(18px)` (topbar, hero device, cap-panel) over `rgba(22, 27, 34, 0.68–0.72)`. Used on every "elevated" surface in the workspace shell.

**Transparency:** widely used — accent colours appear at `0.10`, `0.12`, `0.14`, `0.16`, `0.20`, `0.24` for tinted surfaces, borders, and gradient stops. Pure flat colour fills are reserved for primary buttons.

**Imagery vibe:** when present (hero shot cards), images are slightly desaturated (`saturate(0.92) contrast(1.04)`) and overlaid with a tonal gradient (`linear-gradient(135deg, color-mix(in srgb, var(--frame-tone) 34%, transparent), transparent 42%)`) so they always tonally match the surface. Cool / blue-leaning. No grain on the images themselves; the page-level grain handles that.

**Corner radii:** `4 / 8 / 12 / 16` px tokens **plus** larger marketing radii — workspace sidebar uses `28 px`, hero device `34 px`, hero shot cards `24 px`, pill buttons `999 px`. Workspace cards override the base radius up to `24 px` for a softer, app-shell feel.

**Card anatomy:** subtle border + 24-px padding + 4-px-or-12-px radius + `--shadow-card`. Bento cards add an optional **2 px coloured top accent strip** (`accent="var(--accent)"`) and a coloured glow on hover.

**Focus ring:** `0 0 0 3px rgba(88, 166, 255, 0.3)` — never an outline, always a soft ring matching the accent.

**Layout rules:** sidebar is fixed-position on workspace surfaces (`260 px` base, `290 px` glass variant). Marketing nav is fixed and fades to `rgba(13,17,23,0.82)` + 14-px backdrop blur after 60 px scroll. Content max-width is `1440 px` in the workspace, `1400 px` on landing.

## Iconography

- **Primary set:** [Lucide React](https://lucide.dev/) — used everywhere. Stroke-based, 1.5 px weight, square caps. Default sizes 14 / 16 / 18 / 22 / 28 px.
- **Specific icons in production:** `Wand2` (logo glyph), `LayoutDashboard`, `UploadCloud`, `Download`, `Library`, `Shield`, `LogOut`, `CheckSquare`, `Users`, `Activity`, `AlertTriangle`, `Settings`, `Zap`, `Scissors`, `Grid3X3`, `BarChart3`, `CheckCircle`, `AlertCircle`, `Film`, `Video`, `XOctagon`, `TrendingUp`, `Clock`, `Copy`, `Upload`, `RefreshCw`, `FileVideo`, `Loader2`, `Eye`, `EyeOff`, `Inbox`.
- Icon colour follows context: `var(--accent)` on the primary mark, `var(--text-secondary)` on nav, status colour for state icons.
- **No icon font.** No SVG sprite. No PNG icons. Everything is JSX components from `lucide-react`.
- **Logo:** wordmark "EditEase" set in Inter 700 with `-0.025em` letter-spacing, paired with a `42 × 42 px` glass mark — `rgba(88,166,255,0.10)` background, `1 px rgba(88,166,255,0.20)` border, `14 px` radius, holding a `Wand2` glyph in `var(--accent)`. (The `.workspace-logo-mark` and `.auth-brand-icon` patterns.)
- **Emoji:** appear only inside the react-joyride onboarding tour (🎬 📊 ⬆️ 🔍 ✨ ⚡) and one empty-state hint (📂). Never in chrome, headings, buttons, or product copy.
- **Unicode glyphs:** the right-pointing arrow `→` is the only unicode "icon" used in CTAs ("Get Started →", "Open Workspace →"). The down arrow `↓` appears once on "See how it works ↓".
- **Decorative dots:** macOS traffic-light dots (`#ff5f57`, `#febc2e`, `#28c840`) appear on the hero device topbar and review-window preview header. Pulse dots are a 7–8 px circle in the relevant status colour with a `pulse-ring` keyframe (currentColor box-shadow expanding to 8 px).
- **Stars** in testimonials are the `★` unicode glyph in `#febc2e`.

## Caveats / substitutions

- **Inter** and **JetBrains Mono** are loaded from Google Fonts (matching production); no `.ttf` files needed.
- The repo's actual `vite.svg` favicon is the default Vite logo — it has been kept in `assets/` for parity but the brand mark should be the `Wand2`-in-glass treatment shown across the product.

