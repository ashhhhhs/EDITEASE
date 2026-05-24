# Web App UI Kit — EditEase

A high-fidelity recreation of the EditEase web app. Surfaces covered:

- **Landing peek** — hero, capabilities, review-workspace preview, marquee
- **Workspace** — sidebar nav, top bar, dashboard stats + activity, review queue grid, organized videos shelf
- **Auth** — login card with split layout

Files:
- `index.html` — interactive click-thru shell with all screens
- `Workspace.jsx` — sidebar + topbar shell + dashboard / review / library views
- `Landing.jsx` — landing peek (hero + workspace preview)
- `Auth.jsx` — login screen

Source of truth: `/frontend/src/Landing.jsx`, `AppShell.jsx`, `Dashboard.jsx`, `Login.jsx`, `landing.css`, `index.css`, `auth.css`.

Substitutions (flagged):
- Fonts → Google Fonts CDN (`Inter`, `JetBrains Mono`)
- Icons → `lucide-static` via CDN-rendered SVGs (matches the app's `lucide-react`)
- Hero thumbnails → solid color tiles (real footage thumbnails not committed to repo)
