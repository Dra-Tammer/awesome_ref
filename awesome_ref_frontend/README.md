# AwesomeRef Frontend

Vue 3 single-page application for the AwesomeRef literature reference management tool.

## Tech Stack

- **Framework**: Vue 3 (Composition API)
- **Build Tool**: Vite 6
- **HTTP**: Fetch API (no axios dependency)
- **Styling**: CSS with light/dark theme via `data-theme` attribute

## Project Structure

```
awesome_ref_frontend/
├── index.html
├── vite.config.js
├── package.json
├── dist/                 # Production build output
└── src/
    ├── main.js           # Vue app entry
    ├── App.vue           # Root component, layout orchestration
    ├── style.css         # Global styles and theme variables
    ├── components/
    │   ├── LoginPage.vue       # Login / register form
    │   ├── Toolbar.vue         # Top bar: new reference, import, export, theme, menu
    │   ├── GroupList.vue       # Left sidebar: group navigation
    │   ├── ReferenceList.vue   # Center: reference list with search and clear
    │   ├── ReferenceDetail.vue # Right panel: reference detail with PDF link
    │   ├── ReferenceEditor.vue # New reference modal: manual form + BibTeX parsing
    │   ├── NoteEditor.vue      # Markdown note editor for a reference
    │   ├── DropOverlay.vue     # Drag-and-drop overlay for RIS file import
    │   └── ConfirmDialog.vue   # Reusable confirmation dialog
    ├── composables/
    │   ├── useAuth.js          # Auth state, login/register/logout/password change
    │   ├── useReferences.js    # Reference CRUD, trash, filtering, sorting
    │   ├── useGroups.js        # Group CRUD and lookup
    │   ├── useNotes.js         # Notes CRUD
    │   ├── useTheme.js         # Light/dark theme toggle with transition
    │   └── useToast.js         # Toast notification system
    └── utils/
        ├── risParser.js        # RIS file format parser
        ├── bibtexParser.js     # BibTeX format parser
        └── highlight.js        # Search keyword highlighting
```

## Features

- **Manual creation** — Full-featured form to create references from scratch
- **BibTeX parsing** — Paste BibTeX entries, parse into editable form fields
- **Reference browsing** — Filter by group, search by keyword with clear button
- **RIS import** — Drag and drop or file picker to bulk import `.ris` files
- **PDF linking** — Upload, view, replace, or remove PDF files per reference
- **Group management** — Create, rename, delete groups; assign references to groups
- **Notes** — Write and edit per-reference reading notes
- **Data backup** — Export entire library as JSON; import to restore
- **Trash** — Soft-delete with restore; 30-day auto-purge on the backend
- **Dark mode** — Toggle with smooth CSS transition; persisted in localStorage
- **Keyboard navigation** — Arrow keys to navigate references, Enter to open detail

## Development

```bash
# Install dependencies
npm install

# Start dev server (http://localhost:5173)
npm run dev
```

The dev server proxies API requests to `http://localhost:8000` (configure in `vite.config.js`).

## Production Build

```bash
npm run build
```

Output goes to `dist/`. The FastAPI backend serves these files automatically when present, so no separate web server is needed.

## Composables API

| Composable | Key Exports | Description |
|------------|------------|-------------|
| `useAuth` | `login`, `register`, `logout`, `changePassword`, `isLoggedIn`, `getHeaders` | JWT auth state and methods |
| `useReferences` | `filteredReferences`, `selectedReference`, `addReferences`, `uploadPdf`, `deletePdf`, `softDeleteRef`, `restoreRef`, `clearTrash` | Reference list state, CRUD, and PDF linking |
| `useGroups` | `groups`, `addGroup`, `deleteGroup`, `renameGroup`, `getGroupName` | Group state and CRUD |
| `useNotes` | `notes`, `saveNote`, `deleteNote` | Per-reference notes |
| `useTheme` | `theme`, `toggle` | Light/dark theme |
| `useToast` | `showToast` | Notification toasts |
