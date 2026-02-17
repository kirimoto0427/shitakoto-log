# CLAUDE.md — kiri-apps

## Project Overview

**kiri-apps** is a collection of lightweight, self-contained web applications for personal ADHD management and daily life tracking. All UI text is in Japanese. The apps are deployed as static files on GitHub Pages at `https://kirimoto0427.github.io/kiri-apps/`.

## Repository Structure

```
kiri-apps/
├── index.html              # Portal page — links to all apps
├── shitakoto-log/          # "したことログ" — task completion log
├── todo-1/                 # "今日のすること" — daily todo list
├── tanoshisa/              # "楽しさ塊回収メモ" — happiness log (full)
├── tanoshisa-2/            # "楽しさ塊回収メモ（シンプル）" — happiness log (simple)
├── adhd-quick-reset/       # "ADHDクイックリセット" — 3-min timer + next action
├── adhd-app-1/             # "ラベリングログ" — mental state labeling
├── adhd-app-2/             # "停止・回復ログ" — stop/recovery log
├── adhd-app/               # Stub (empty)
├── adhd-timer/             # Stub (empty)
├── urge-log/               # Stub (empty)
└── README.md               # App URL directory (Japanese)
```

Each app is a single `index.html` file with embedded CSS and JavaScript. There are no external dependencies, no build steps, and no package manager.

## Tech Stack

| Layer       | Technology                                    |
|-------------|-----------------------------------------------|
| Language    | Vanilla JavaScript (ES6+), no TypeScript      |
| Markup      | HTML5                                         |
| Styling     | CSS3 with custom properties, embedded in HTML |
| Frameworks  | None — no React, Vue, or other libraries      |
| Data        | `localStorage` only (no backend, no APIs)     |
| Deployment  | GitHub Pages (static files, no CI/CD)         |
| Testing     | None                                          |
| Linting     | None                                          |

## Development Workflow

There is no build system. To develop:

1. Edit the `index.html` file inside the relevant app directory.
2. Open the file in a browser to test.
3. Commit and push to deploy via GitHub Pages.

### Adding a New App

1. Create a new directory at the repo root (e.g., `my-app/`).
2. Add an `index.html` file following the conventions below.
3. Add a link card to the portal in `index.html` (root).
4. Add a URL entry to `README.md`.

## Code Conventions

### File Structure

Each app is a single HTML file with this structure:

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>App Title</title>
  <style>
    /* All CSS here — no external stylesheets */
  </style>
</head>
<body>
  <!-- HTML markup -->
  <script>
    /* All JavaScript here — no external scripts */
  </script>
</body>
</html>
```

### CSS Design System

All apps use CSS custom properties defined in `:root`:

```css
:root {
  --bg: #f6f8ff;          /* Page background */
  --card: #ffffffcc;      /* Card background (semi-transparent) */
  --ink: #1b1f2a;         /* Primary text */
  --sub: #556070;         /* Secondary/muted text */
  --accent: #4b7cff;      /* Primary action color (blue) */
  --accent2: #e9f0ff;     /* Light accent background */
  --danger: #e05555;      /* Destructive action color (red) */
  --line: #e6ecf6;        /* Borders and dividers */
  --shadow: 0 10px 30px rgba(20,30,60,.12);
  --radius: 16px–18px;    /* Card corner radius */
}
```

Common visual patterns:
- **Glassmorphic cards**: `background: var(--card)` with `backdrop-filter: blur()` and subtle borders
- **Pill buttons**: `border-radius: 999px` for tabs and tags
- **Hover lift**: `transform: translateY(-2px)` on interactive cards
- **Font stack**: `system-ui, -apple-system, "Segoe UI", Roboto, "Hiragino Sans", "Noto Sans JP", "Yu Gothic", sans-serif`
- **Responsive**: Grid/flex layouts, breakpoints at ~520px and ~860px

### JavaScript Patterns

**Section organization** — code is divided by labeled comment blocks:

```javascript
// ========= 設定 =========        (Configuration/constants)
// ========= 状態 =========        (State)
// ========= ユーティリティ =========  (Utilities)
// ========= 追加/削除 =========     (Add/Delete operations)
// ========= UI描画 =========       (Rendering)
// ========= イベント =========      (Event binding)
// ========= 起動 =========        (Initialization — runs at bottom)
```

**DOM access** — either direct `document.getElementById()` or a shorthand:

```javascript
const $ = (id) => document.getElementById(id);
```

**State and persistence** — simple objects stored in `localStorage`:

```javascript
const STORAGE_KEY = "appName_v1";
function save() { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }
function load() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); }
  catch(e) { return []; }
}
```

**ID generation** — client-side random IDs:

```javascript
// Preferred (when available)
crypto.randomUUID()
// Fallback
"id_" + Math.random().toString(16).slice(2) + "_" + Date.now().toString(16)
```

**Date formatting** — custom Japanese-locale helpers in each app:

```javascript
const pad2 = (n) => String(n).padStart(2, "0");
// Produces: "2026/02/17(火)"
```

**Rendering** — imperative DOM creation via `document.createElement()` and `innerHTML`. No virtual DOM or templating library.

**HTML escaping** — when using `innerHTML`, user-provided text is escaped:

```javascript
function escapeHtml(s) {
  return String(s)
    .replaceAll("&","&amp;").replaceAll("<","&lt;")
    .replaceAll(">","&gt;").replaceAll('"',"&quot;")
    .replaceAll("'","&#39;");
}
```

## Key Rules for AI Assistants

1. **Keep apps self-contained.** Each app must be a single `index.html` file with all CSS and JS inline. Do not introduce external dependencies, bundlers, or build steps.
2. **Preserve the design system.** Use the existing CSS custom properties (`--accent`, `--card`, `--line`, etc.) and visual patterns (glassmorphic cards, pill buttons, hover lifts).
3. **Use localStorage for persistence.** Follow the existing pattern of versioned keys (e.g., `appName_v1`) and JSON serialization. Never assume a backend.
4. **Keep Japanese UI text.** All user-facing text is in Japanese. Maintain this convention.
5. **Follow the section comment structure.** Organize JavaScript with the labeled comment blocks (設定, 状態, ユーティリティ, etc.).
6. **Mobile-first responsive design.** All apps must work well on phones. Use flex/grid layouts with appropriate breakpoints.
7. **No over-engineering.** This is a simple static site. Do not add TypeScript, frameworks, linters, or package managers unless explicitly requested.
8. **Escape user input.** When rendering user-provided text with `innerHTML`, always use `escapeHtml()` to prevent XSS.
9. **Update the portal.** When adding a new app, add a card entry to the root `index.html` and a URL entry to `README.md`.
