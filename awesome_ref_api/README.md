# AwesomeRef API

Backend service for AwesomeRef, a literature reference management tool. Built with FastAPI and SQLAlchemy, backed by MySQL.

## Tech Stack

- **Framework**: FastAPI
- **ORM**: SQLAlchemy (declarative base)
- **Database**: MySQL 8.0+ (via PyMySQL)
- **Auth**: JWT (python-jose) + SHA-256 salted passwords

## Project Structure

```
awesome_ref_api/
├── main.py           # App entry point, middleware, router registration
├── database.py       # SQLAlchemy engine, session factory, Base
├── models.py         # ORM models: User, Reference, Note, Group
├── auth_utils.py     # Password hashing, JWT encode/decode, user init
├── deps.py           # FastAPI dependencies (get_current_user)
├── init_db.py        # Database initialization helper
└── routers/
    ├── auth.py       # POST /login, /register, /change-password
    ├── references.py # CRUD, trash, restore, group assignment
    ├── notes.py      # CRUD for per-reference notes
    ├── groups.py     # Create, rename, delete groups
    └── export.py     # GET /export, POST /import (full data backup)
```

## Data Models

| Model | Description |
|-------|-------------|
| `User` | Account with username and salted password hash |
| `Reference` | Academic reference (title, authors, journal, DOI, abstract, keywords, etc.) |
| `Note` | Markdown note attached to a reference (per user) |
| `Group` | User-defined group for organizing references (many-to-many via `ref_group_assoc`) |

## API Endpoints

### Auth (`/api/auth`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/login` | Login, returns JWT token |
| POST | `/register` | Register new user |
| POST | `/change-password` | Change password (requires auth) |

### References (`/api`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/references` | List all active references |
| POST | `/references` | Import references (supports upsert) |
| DELETE | `/references/{ref_key}` | Soft-delete (move to trash) |
| POST | `/references/{ref_key}/restore` | Restore from trash |
| DELETE | `/references/{ref_key}/permanent` | Permanently delete |
| GET | `/references/trash` | List trashed references |
| DELETE | `/references/trash` | Empty trash |
| POST | `/references/{ref_key}/groups/{group_key}` | Add reference to group |
| DELETE | `/references/{ref_key}/groups/{group_key}` | Remove reference from group |

### Notes (`/api`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/notes` | Get all notes for current user |
| POST | `/notes` | Create or update a note |
| DELETE | `/notes/{ref_key}` | Delete a note |

### Groups (`/api`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/groups` | List all groups |
| POST | `/groups` | Create a new group |
| PUT | `/groups/{group_key}` | Rename a group |
| DELETE | `/groups/{group_key}` | Delete a group |

### Export (`/api`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/export` | Export all data (groups, references, notes) as JSON |
| POST | `/import` | Import data from JSON backup |

## Configuration

All configuration is via environment variables. Copy `.env.example` to `.env` and edit:

```bash
cp .env .env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `AWESOMEREF_DB_USER` | `root` | MySQL username |
| `AWESOMEREF_DB_PASSWORD` | (empty) | MySQL password |
| `AWESOMEREF_DB_HOST` | `localhost` | MySQL host |
| `AWESOMEREF_DB_PORT` | `3306` | MySQL port |
| `AWESOMEREF_DB_NAME` | `awe_ref` | Database name |
| `AWESOMEREF_SECRET_KEY` | (built-in default) | JWT signing secret — **change in production** |

## Installation

```bash
pip install fastapi uvicorn sqlalchemy pymysql python-jose[cryptography] python-multipart
```

## Run

```bash
# Development (auto-reload)
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API docs available at `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc` (ReDoc).
