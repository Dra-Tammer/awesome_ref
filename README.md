# AwesomeRef

A lightweight, self-hosted literature reference management tool built with FastAPI and Vue 3.

AwesomeRef helps researchers and students organize academic references, take notes, and manage reading groups — all in one clean interface.

## Features

- **RIS Import** — Import references directly from `.ris` files exported by Zotero, EndNote, and other reference managers
- **Reference Management** — Full CRUD with support for title, authors, journal, DOI, abstract, keywords, and more
- **Grouping** — Organize references into custom groups; ungrouped references are automatically collected
- **Notes** — Attach rich-text notes to each reference for reading summaries and annotations
- **Trash & Restore** — Soft-delete with 30-day auto-purge; restore accidentally deleted references anytime
- **Data Export / Import** — Export your entire library as JSON for backup or migration; import to restore
- **Multi-User** — JWT-based authentication with user registration and password management
- **Dark Mode** — Built-in light / dark theme toggle
- **Responsive UI** — Clean, modern interface built with Vue 3

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, SQLAlchemy, MySQL |
| Frontend | Vue 3, Vite |
| Auth | JWT (python-jose), SHA-256 salted passwords |
| ORM | SQLAlchemy (declarative) |

## Project Structure

```
awesome_ref/
├── awesome_ref_api/          # Backend (FastAPI)
│   ├── main.py               # App entry, middleware, router registration
│   ├── database.py           # SQLAlchemy engine & session
│   ├── models.py             # ORM models: User, Reference, Note, Group
│   ├── auth_utils.py         # Password hashing, JWT creation & verification
│   ├── deps.py               # Dependency injection (current user)
│   └── routers/
│       ├── auth.py           # Login, register, change password
│       ├── references.py     # Reference CRUD, trash, group assignment
│       ├── notes.py          # Notes CRUD
│       ├── groups.py         # Group management
│       └── export.py         # Data export & import
├── awesome_ref_frontend/     # Frontend (Vue 3 + Vite)
│   ├── src/
│   │   ├── App.vue
│   │   ├── components/       # UI components
│   │   ├── composables/      # Vue composables (auth, theme, etc.)
│   │   └── utils/            # RIS parser, highlight utility
│   └── dist/                 # Production build (served by FastAPI)
└── .gitignore
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- MySQL 8.0+

### 1. Database Setup

Create a MySQL database:

```sql
CREATE DATABASE awe_ref CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Update the connection settings in `awesome_ref_api/database.py`:

```python
DB_USER = "root"
DB_PASSWORD = "your_password"
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "awe_ref"
```

### 2. Backend

```bash
cd awesome_ref_api

# Install dependencies
pip install fastapi uvicorn sqlalchemy pymysql python-jose[cryptography] python-multipart

# Start the server (development)
python main.py
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd awesome_ref_frontend

# Install dependencies
npm install

# Development server
npm run dev

# Production build
npm run build
```

The dev server runs at `http://localhost:5173`. In production, FastAPI serves the built files from `dist/` automatically.

## API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | User login |
| `/api/auth/register` | POST | User registration |
| `/api/auth/change-password` | POST | Change password |
| `/api/references` | GET | List all references |
| `/api/references` | POST | Import references (RIS parsed) |
| `/api/references/{ref_key}` | DELETE | Soft-delete a reference |
| `/api/references/{ref_key}/restore` | POST | Restore from trash |
| `/api/references/trash` | GET | List trash |
| `/api/references/{ref_key}/groups/{group_key}` | POST | Add reference to group |
| `/api/groups` | GET / POST | List or create groups |
| `/api/notes` | GET / POST | List or save notes |
| `/api/export` | GET | Export all data as JSON |
| `/api/import` | POST | Import data from JSON |

Full interactive documentation is available at `/docs` when the server is running.

## Configuration

Default users are created automatically on first run (defined in `auth_utils.py`). Change the `SECRET_KEY` in `auth_utils.py` before deploying to production.

## License

MIT
