# JanSamadhan AI — E-Governance Grievance Portal

An AI-ready public grievance redressal portal enabling citizens to file, attach evidence to, and track civic complaints across municipal departments in English, Hindi, and Hinglish.

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-%3E%3D0.115-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-15-000000?logo=next.js&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Default_Local_DB-003B57?logo=sqlite&logoColor=white)

---

## Features

- **Citizen Portal (Next.js App Router)**:
  - Home page with quick Ticket ID lookup (`/`)
  - Dual login supporting Citizen Mock OTP and Staff Email/Password (`/login`)
  - Grievance filing form with GPS coordinate auto-detection, ward selection, language selection (`en` / `hi` / `hinglish`), and multi-file photo/PDF uploads (`/submit`)
  - Anonymous complaint filing generating a private `ANON-XXXXXXXX` tracking code
  - Public ticket tracking without login (`/track`) showing a 5-stage progress timeline (`Submitted` → `Assigned` → `In Progress` → `Resolved` → `Closed`)
  - Authenticated `"My Complaints"` view with status filtering and pagination (`/my-complaints`)
  - Light/dark theme toggle respecting system `prefers-color-scheme`
- **Backend & Governance Core (FastAPI + SQLAlchemy)**:
  - Multilingual rule-based department auto-detection (`water`, `electricity`, `roads`, `sanitation`, `health`, `police`, or `general` fallback)
  - Validated file uploads (`.jpg`, `.jpeg`, `.png`, `.webp`, `.pdf`; MIME type and max 5 MB size checks)
  - JWT authentication with `bcrypt` password hashing and RBAC roles (`citizen`, `officer`, `dept_head`, `district_head`, `admin`)
  - PII-masked JSON structured logging (redacts Indian phone numbers and email addresses in logs)
  - Automatic SQLite schema creation and idempotent seed data on backend startup, alongside Alembic migrations

---

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | Next.js (`^15.1.6`, App Router), React (`^19.0.0`), TypeScript (`^5.7.2`), Tailwind CSS (`^4.0.0`), `lucide-react` |
| **Backend** | FastAPI (`>=0.115.0`), Uvicorn (`>=0.32.0`), Pydantic (`>=2.10.0`), `pydantic-settings` |
| **Database & ORM** | SQLAlchemy (`>=2.0.36`), Alembic (`>=1.14.0`), SQLite (default local dev; PostgreSQL-compatible via `DATABASE_URL`) |
| **Auth & Security** | PyJWT (`>=2.10.0`), `bcrypt` (`>=4.2.0`), `pyotp` (`>=2.9.0`) |
| **Background Scheduler** | APScheduler (`>=3.10.4`) |
| **Testing** | `pytest` (`>=8.3.0`), `httpx` (`>=0.28.0`) |

---

## Project Structure

```text
E-Governance Grievance/
├── .env.example
├── .gitignore
├── README.md
├── backend/
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── requirements-ml.txt            # Optional ML/LLM extras (not required to run locally)
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── f8c92371fc02_initial_schema.py
│   ├── app/
│   │   ├── main.py                    # FastAPI app, CORS, /health, lifespan auto-seed
│   │   ├── seed.py                    # Idempotent departments, wards, SLA rules, users, sample tickets
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── logging.py
│   │   │   └── security.py
│   │   ├── models/
│   │   │   ├── governance.py          # notifications, sla_rules, escalation_rules, escalations, ai_overrides, audit_logs, faq_documents
│   │   │   ├── grievance.py           # grievances, attachments, status_history, feedback
│   │   │   ├── organization.py        # departments, wards, officers
│   │   │   └── user.py                # users, otp_codes
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── grievances.py
│   │   │   └── reference.py
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   └── grievance.py
│   │   └── services/
│   │       ├── auth_service.py
│   │       ├── classifier.py          # Rule-based EN/HI/Hinglish department classifier
│   │       ├── grievance_service.py
│   │       └── storage_service.py
│   └── tests/
│       ├── conftest.py
│       ├── test_classifier.py
│       └── test_phase1.py
└── frontend/
    ├── next.config.ts
    ├── package.json
    ├── postcss.config.mjs
    ├── tsconfig.json
    └── src/
        ├── app/
        │   ├── globals.css
        │   ├── layout.tsx
        │   ├── page.tsx               # Home + quick ticket lookup
        │   ├── login/page.tsx         # Citizen OTP + Staff login
        │   ├── submit/page.tsx        # File complaint form
        │   ├── track/page.tsx         # Public ticket tracker
        │   └── my-complaints/page.tsx # Citizen complaints dashboard
        ├── components/
        │   ├── Navbar.tsx
        │   └── StatusTimeline.tsx
        └── lib/
            └── api.ts
```

---

## Getting Started (Windows PowerShell)

> **Note:** Both the backend and frontend terminals must remain open while running the app locally.

### 1. Clone the repository

```powershell
git clone https://github.com/surajagrahari76/egov-grievance.git
cd egov-grievance
```

### 2. Backend Setup

```powershell
# Create and activate virtual environment
python -m venv backend\.venv
.\backend\.venv\Scripts\Activate.ps1

# Install core backend dependencies
pip install -r backend\requirements.txt

# Copy environment template
Copy-Item .env.example .env

# Run database migrations (optional — tables and seed data also initialize automatically on startup)
cd backend
..\backend\.venv\Scripts\alembic upgrade head

# Start FastAPI server (SQLite DB and demo seed data are created automatically)
..\backend\.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend URLs:
- API Base: `http://127.0.0.1:8000/api/v1`
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`

### 3. Frontend Setup (New PowerShell Terminal)

```powershell
cd frontend
npm install
npm run dev -- --port 3000
```

Frontend URL: `http://localhost:3000`

---

## Environment Variables

Defined in [`.env.example`](.env.example):

| Variable | Description |
| :--- | :--- |
| `APP_ENV` | Application environment (`dev`, `staging`, or `prod`) |
| `APP_NAME` | Display title used in FastAPI OpenAPI metadata |
| `SECRET_KEY` | Signing secret for JWT tokens (replace in production) |
| `JWT_ALGORITHM` | JWT signing algorithm (default `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime in minutes |
| `DATABASE_URL` | SQLAlchemy database URL (defaults to local SQLite `grievance_dev.db`) |
| `JOB_RUNNER` | Background job runner (`apscheduler` for local dev) |
| `REDIS_URL` | Redis connection URL (reserved for optional caching/Celery) |
| `AI_PROVIDER` | AI mode (`fallback` uses built-in deterministic rules) |
| `GEMINI_API_KEY` | Optional Gemini API key (leave blank for rule-based fallback) |
| `OPENAI_API_KEY` | Optional OpenAI API key (leave blank for rule-based fallback) |
| `UPLOAD_DIR` | Local directory for storing uploaded grievance attachments |
| `MAX_UPLOAD_SIZE_MB` | Maximum allowed upload size per file in megabytes |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins |
| `DEMO_MODE` | Enables deterministic demo OTP (`123456`) for demo citizen login |

---

## Demo Credentials (Local Testing Only)

> **Warning:** These accounts are seeded automatically by `backend/app/seed.py` for local development and testing only. Do not use them in production.

### Citizen (Mock SMS OTP)
- **Phone:** `9876543210`
- **Mock OTP:** `123456` *(also printed to the backend console via `[MOCK SMS OTP]`)*

### Staff Accounts (Email & Password)

| Role | Email | Password | Scope |
| :--- | :--- | :--- | :--- |
| `admin` | `admin@demo.gov.in` | `Admin123!` | System-wide |
| `district_head` | `district@demo.gov.in` | `Officer123!` | District Magistrate Nodal |
| `dept_head` | `depthead.water@demo.gov.in` | `Officer123!` | Water Supply & Jal Board |
| `officer` | `officer.water@demo.gov.in` | `Officer123!` | Water Supply (`W-01` Connaught Place) |
| `officer` | `officer.roads@demo.gov.in` | `Officer123!` | Roads & PWD (`W-02` Karol Bagh) |

### Seeded Sample Tickets
- `GRV-2026-100001` (Water Supply — `in_progress`)
- `GRV-2026-100002` (Roads — `assigned`)
- `GRV-2026-100003` (Electricity — `submitted`, anonymous tracking code: `ANON-DEMO1234`)

---

## Main API Endpoints

Interactive Swagger documentation is available at **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** (OpenAPI schema: `/api/v1/openapi.json`).

| Method | Path | Purpose |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health, DB dialect, and runtime mode check |
| `POST` | `/api/v1/auth/otp/request` | Generate and log a mock SMS OTP for citizen login |
| `POST` | `/api/v1/auth/otp/verify` | Verify citizen OTP and return a JWT access token |
| `POST` | `/api/v1/auth/login` | Authenticate officer/admin user with email and password |
| `GET` | `/api/v1/auth/me` | Return the currently authenticated user profile |
| `POST` | `/api/v1/grievances` | Submit a new grievance (multipart form with optional files & anonymous mode) |
| `GET` | `/api/v1/grievances/mine` | Paginated list of the logged-in citizen's complaints |
| `GET` | `/api/v1/grievances/track/{ticket_id}` | Public ticket tracking (supports `?anonymous_code=ANON-...`) |
| `GET` | `/api/v1/grievances/{ticket_id}` | Detailed grievance view (owner-scoped for citizens) |
| `GET` | `/api/v1/grievances/rbac-check/staff-only` | RBAC verification endpoint for staff roles |
| `GET` | `/api/v1/reference/departments` | List active departments |
| `GET` | `/api/v1/reference/wards` | List municipal wards/zones |

---

## Auto Department Detection

When a citizen submits a complaint with **Auto-detect (Default)** (empty `category`), `create_grievance()` calls `classify_department(db, f"{payload.title} {payload.text}")` in `backend/app/services/classifier.py`:

1. Combines and lowercases the complaint title and description.
2. Scores each department by counting keyword matches across English, Hinglish (Roman Hindi), and Hindi (Devanagari) — using letter-boundary matching for ASCII tokens and substring matching for Devanagari.
3. Assigns the highest-scoring active `Department` (`dept_id` + `category`). If no keywords match, it falls back to `category="general"` (`dept_id=None`). Manual category selection always takes precedence.

| Department Code | Department Name | Sample Keywords (`classifier.py`) |
| :--- | :--- | :--- |
| `water` | Water Supply & Jal Board | `water`, `water supply`, `paani`, `pani`, `jal`, `tanker`, `pipeline`, `पानी`, `नल`, `टैंकर` |
| `electricity` | Electricity & Power Distribution | `electricity`, `power cut`, `transformer`, `streetlight`, `bijli`, `batti`, `बिजली`, `विद्युत` |
| `roads` | Roads & Public Works (PWD) | `road`, `pothole`, `footpath`, `flyover`, `sadak`, `gadda`, `gaddha`, `सड़क`, `गड्ढा` |
| `sanitation` | Sanitation & Solid Waste | `sanitation`, `garbage`, `drain`, `sewage`, `kachra`, `safai`, `nali`, `कचरा`, `सफाई`, `नाली` |
| `health` | Public Health & Hospitals | `health`, `hospital`, `doctor`, `medicine`, `ambulance`, `dengue`, `dawai`, `अस्पताल`, `दवाई` |
| `police` | Law & Order / Municipal Safety | `police`, `theft`, `harassment`, `safety`, `fir`, `chori`, `suraksha`, `thana`, `पुलिस`, `चोरी` |

---

## Running Tests

Run the backend `pytest` suite from the `backend/` directory:

```powershell
cd backend
..\backend\.venv\Scripts\pytest -v
```

Frontend typecheck and production build check:

```powershell
cd frontend
npm run typecheck
npm run build
```

---

## Roadmap

- [ ] Real SMS OTP gateway integration (replace mock console OTP)
- [ ] Officer and Admin dashboards in the frontend (status updates, SLA escalation matrix, analytics)
- [ ] ML-based complaint classification, semantic duplicate detection, and chatbot/RAG (`requirements-ml.txt`)
- [ ] Production deployment setup (Docker Compose, PostgreSQL, Redis, CI/CD)

---

## Author

**Suraj Agrahari** — [https://github.com/surajagrahari76](https://github.com/surajagrahari76)
