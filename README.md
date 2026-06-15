# Student Society & Welfare Portal

A multi-tenant backend for managing student societies and a shared welfare feed. Societies maintain a public profile and list of executive contacts, while administrators post welfare updates and announcements. Access is controlled by a role hierarchy, and each community administrator is scoped to only the societies they actually manage.

The backend is built with FastAPI, SQLModel, and PostgreSQL. A frontend (Next.js) is planned and will be added under `frontend/`.

> **Status:** Backend complete and tested. Frontend in progress.

---

## Table of contents

- [Features](#features)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Data model](#data-model)
- [API endpoints](#api-endpoints)
- [Getting started](#getting-started)
- [Design decisions](#design-decisions)

---

## Features

- **Role-based access control** with two roles: a global `super_admin` and a scoped `community_admin`.
- **Multi-tenancy.** A `community_admin` can only post and edit within societies they are explicitly assigned to, enforced server-side through a junction table.
- **Public society directory.** Anyone can browse societies, filter by category, and view a society profile with its ordered list of executive contacts.
- **Welfare feed.** A public, paginated feed sorted by pinned status, then urgency, then recency.
- **Stateless JWT authentication** with bcrypt password hashing.
- **Idempotent database seeding** from a JSON file, plus automatic creation of a default super admin.

---

## Tech stack

| Layer | Choice |
|---|---|
| Web framework | FastAPI |
| ORM / models | SQLModel (SQLAlchemy + Pydantic) |
| Database | PostgreSQL |
| Auth | JWT (python-jose), bcrypt via passlib |
| Config | pydantic-settings |
| Server | Uvicorn |

---

## Project structure

```
society-portal/
  backend/
    app/
      config.py          # Typed settings loaded and validated from .env
      database.py         # Engine, table creation, session dependency
      models.py           # SQLModel tables (the five core entities)
      security.py         # Password hashing, JWT, auth dependency, role guard
      main.py             # FastAPI app, router registration
      api/
        v1/
          auth.py         # Login -> JWT
          societies.py    # Public directory + protected profile update
          welfare.py      # Public feed + protected post creation
    seed.py               # Builds tables, seeds societies, creates super admin
    seed.json             # Initial society + executive contact data
    requirements.txt
  frontend/               # Planned (Next.js)
```

All Python imports are absolute from the `app` package, so the server is run from inside `backend/`.

---

## Data model

Five entities. Every primary key is a UUID.

- **User** — login accounts. Holds the role (`super_admin` / `community_admin`), a hashed password, and an `is_active` flag.
- **Society** — a society's public profile: name, unique slug, category, description, and optional links.
- **SocietyAdmin** — a junction table linking a `User` to a `Society`. This is the source of truth for which societies a community admin manages. Because it carries no uniqueness constraint on either side, one admin can manage several societies and one society can have several admins.
- **ExecutiveContact** — the people displayed on a society's profile (name, role, contact links, and an `order_weight` controlling display order). These are display data, not login accounts.
- **WelfarePost** — a feed post. Belongs to a society, or to none (a global bulletin). Carries a category, an urgency level, a pinned flag, and a timestamp.

The relationships all radiate from `Society`: admins, executive contacts, and posts each reference a society, but never each other.

---

## API endpoints

All routes are prefixed with `/api/v1`.

### Auth
- `POST /auth/login` — exchange email and password for a JWT.

### Societies
- `GET /societies/` — list societies; optional `?category=` filter.
- `GET /societies/{slug}` — full society profile plus its executive contacts, ordered by `order_weight`.
- `PUT /societies/{id}` — update a society profile. **Protected.** Super admins may edit any society; community admins only their own.

### Welfare
- `GET /welfare/` — public paginated feed, sorted by `is_pinned`, then `urgency_level`, then `created_at`, all descending. Supports `?skip=` and `?limit=`.
- `POST /welfare/` — create a post. **Protected.** Super admins may post anywhere, including global bulletins; community admins only under societies they manage.

Interactive documentation is available at `/docs` when the server is running.

---

## Getting started

### Prerequisites
- Python 3.12+
- PostgreSQL 15+

### 1. Database

Create a database and a user, then grant schema privileges (the schema grant is required on PostgreSQL 15+):

```sql
CREATE DATABASE society_portal;
CREATE USER society_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE society_portal TO society_user;
\c society_portal
GRANT ALL ON SCHEMA public TO society_user;
```

### 2. Environment

From `backend/`, create a `.env` file:

```
DATABASE_URL=postgresql+psycopg://society_user:your_password@localhost:5432/society_portal
ENV=development
SECRET_KEY=<generate one: python3 -c "import secrets; print(secrets.token_hex(32))">
ACCESS_TOKEN_EXPIRE_MINUTES=30
SUPER_ADMIN_EMAIL=admin@example.com
SUPER_ADMIN_PASSWORD=choose_a_strong_password
```

`.env` is gitignored and must never be committed.

### 3. Install

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Seed the database

```bash
python3 seed.py
```

This builds the tables, loads the societies from `seed.json`, and creates the super admin from your `.env` values. It is safe to run more than once.

### 5. Run

```bash
uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000/docs`.

---

## Design decisions

A few choices in here were deliberate, and most of them came out of avoiding a bug rather than chasing elegance.

### Urgency stored as an integer, not a string

The welfare feed sorts by urgency level descending. If urgency were stored as a plain string (`low`, `medium`, `high`, `critical`), PostgreSQL would sort it alphabetically, which puts `medium` above `high` and produces a meaningless priority order. Storing it as an integer behind the label (low=1 … critical=4) makes the descending sort correct and keeps the column cheap to index. The sort columns (`is_pinned`, `urgency_level`, `created_at`) are all indexed, since the feed sorts on them on every request.

### Multi-tenancy lives in a junction table, not on the user

A community admin's reach is defined by rows in `SocietyAdmin`, not by anything on the user record. The `role` column says what tier someone is; the junction says what they can touch. This keeps the two concerns separate and means an admin managing several societies is just several rows, with no schema change.

### Server-side authorization on every write (IDOR defense)

The society a post or edit targets is supplied by the client, so it is never trusted. On every protected write, the server looks up the caller's `SocietyAdmin` rows and confirms membership in the *specific* society being targeted. A community admin for one society cannot act on another by changing the ID in the request; there is no junction row to authorize it. Super admins bypass this check by role.

### Global bulletins are a privilege, not just a nullable column

A `WelfarePost` with no society is a global bulletin. The column is nullable to make that possible, but nullability alone would let a community admin omit the society ID and slip a post into the global feed. So the create endpoint explicitly rejects null-society posts from anyone who is not a super admin. The model defines what is structurally possible; the endpoint defines what is permitted.

### `is_active` is checked on every request, not just at login

JWTs are stateless, so a deactivated user keeps a technically valid token until it expires. The auth dependency re-checks `is_active` on every request, which means revoking access takes effect within the token window rather than waiting for expiry.

### Partial updates preserve untouched fields

The society update endpoint accepts a body where every field is optional and applies only the fields the client actually sent. Omitted fields are left as they are rather than overwritten with null, so a request that changes one field does not wipe the rest.

### Idempotent seeding

The seed script checks for existing records before inserting (societies by slug, the super admin by role) so it can be re-run without violating unique constraints. The super admin password is read from the environment rather than hardcoded.

---

## Notes

- `bcrypt` is pinned to `4.0.1` for compatibility with the installed `passlib` release, which reads a version attribute that newer bcrypt versions removed.
- The project is run from inside `backend/` because all imports are absolute from the `app` package and the `.env` is read relative to the working directory.