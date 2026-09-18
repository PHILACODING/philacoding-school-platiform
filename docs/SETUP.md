# School Platform Development Guide

This project is a reusable online learning platform for schools. Applications, uploaded documents, users, assessment questions, answers, and results are designed to be stored in PostgreSQL. The browser keeps only a short-lived signed access token in `sessionStorage` after login; it does not keep school records.

## 1. Project map

```text
philacoding-school-platform/
|-- index.html                 # Current public page and working prototype flows
|-- frontend/
|   |-- assets/images/         # Logos, school photos, event photos, timetables
|   |-- css/mobile.css         # Small-screen production overrides
|   |-- js/api.js              # One browser entry point for backend requests
|-- backend/
|   |-- app/main.py            # FastAPI application and health endpoint
|   |-- app/api/               # Add applications, users, assessments, and school routers here
|   |-- tests/                 # Backend tests
|   |-- requirements.txt       # Python packages for the API
|   |-- .env.example           # Safe environment-variable template
|-- database/
|   |-- schema.sql             # PostgreSQL tables and indexes
|   |-- seed.sql               # Safe local demo school data
|-- docs/SETUP.md              # This guide
|-- scripts/start-backend.ps1  # Windows development server helper
```

### Why this is a professional layout

- `frontend` owns what a learner sees in a browser: HTML, CSS, JavaScript, and optimized images.
- `backend` owns validation, authentication, business rules, file handling, and API responses. A browser must not connect directly to PostgreSQL.
- `database` stores repeatable SQL changes and safe development data.
- `docs` explains the system for another developer or school implementation team.
- `scripts` turns repeated setup commands into a predictable workflow.

The existing `index.html` remains the working entry point for the public page and portal flows. Its large inline CSS and portal script can be extracted gradually into `frontend/css` and `frontend/js` after each feature has a test.

## 2. Tools and responsibilities

### HTML

HTML is the structure and accessible content: navigation, headings, forms, tables, buttons, and image alternatives. It should not contain database credentials or business rules.

### CSS

CSS controls layout, typography, colors, spacing, and responsive behavior. This project favors lightweight CSS and responsive grids so a normal smartphone does not need a heavy application bundle.

### JavaScript

JavaScript provides browser interaction such as the menu, slider, form feedback, and API calls. It calls `window.schoolApi`; applications and assessment records are sent to FastAPI and persisted in PostgreSQL.

### Python and FastAPI

Python is the server-side language. FastAPI exposes small REST endpoints, validates request data, applies school permissions, and calls database code. It is lightweight enough for a small deployment and clear enough for a growing team.

### PostgreSQL

PostgreSQL is the permanent database. It stores schools, users, applications, assessment results, roles, timestamps, and relationships. It is used instead of `localStorage` because browser storage is private to one device, can be cleared, cannot be trusted, and cannot support teacher access across devices.

### Git and GitHub

Git records changes. GitHub stores the repository and can run checks through CI. Never commit passwords, real learner information, uploaded documents, or `.env` files.

## 3. Install the local tools on Windows

1. Install Python 3.11 or newer from `https://www.python.org/downloads/`. During installation, enable **Add Python to PATH**.
2. Install PostgreSQL from `https://www.postgresql.org/download/windows/`. Remember the password created for the `postgres` administrator.
3. Install Git from `https://git-scm.com/download/win`.
4. Open this repository in VS Code.
5. Use the VS Code integrated PowerShell terminal for the commands below.

## 4. Create the PostgreSQL database

### Option A: pgAdmin 4

1. Open pgAdmin 4 and connect to your local PostgreSQL 18 server using the master password chosen during installation.
2. In the left tree, right-click **Login/Group Roles**, choose **Create > Login/Group Role**, and create:
	- Name: `school_app`
	- Definition > Password: choose a private local password
	- Privileges: enable **Can login?**
3. Right-click **Databases**, choose **Create > Database**, and create:
	- Database: `school_platform`
	- Owner: `school_app`
4. Right-click `school_platform`, choose **Query Tool**, open `database/schema.sql`, and execute the complete file.
5. In the same Query Tool, open `database/seed.sql` and execute the complete file.
6. Run this verification query:

```sql
SELECT id, name, slug FROM schools;
SELECT student_number, employee_id, role FROM users;
```

You should see the Siphesihle school, one learner (`26123456`), and one teacher (`T2347233`).

Copy `backend/.env.example` to `backend/.env` and replace `change-me` in `DATABASE_URL` with the password you chose for `school_app`. Keep `backend/.env` private.

### Option B: SQL Shell or psql

Open **SQL Shell (psql)** from the Windows Start menu, or run `psql` in a terminal where PostgreSQL is on `PATH`.

Connect as the PostgreSQL administrator and enter the password chosen during installation. Then run:

```sql
CREATE USER school_app WITH PASSWORD 'change-this-local-password';
CREATE DATABASE school_platform OWNER school_app;
\q
```

Use a strong, private password in a real environment. The example password is only a placeholder.

Now apply the project schema from the repository root:

```powershell
psql -U school_app -d school_platform -f database/schema.sql
psql -U school_app -d school_platform -f database/seed.sql
```

The seed file creates two local-only accounts, both using the temporary password `ChangeMe123!`:

- Learner: student number `26123456`
- Teacher: employee ID `T2347233`

Change or remove these accounts before sharing the application. The seed also creates the Economics 101 question keys used for server-side scoring.

Confirm the starter school exists:

```powershell
psql -U school_app -d school_platform -c "SELECT id, name, slug FROM schools;"
```

Useful PostgreSQL commands:

```text
\l                    list databases
\c school_platform    connect to this database
\dt                   list tables
\d schools            describe a table
\q                    quit psql
```

## 5. Start the Python API

From the repository root:

```powershell
Copy-Item backend/.env.example backend/.env
.\scripts\start-backend.ps1
```

The script creates `backend/.venv`, installs the pinned packages, and starts FastAPI at `http://localhost:8000`.

Check the API in a browser:

- `http://localhost:8000/api/v1/health`
- `http://localhost:8000/docs` for the automatic FastAPI documentation

Start the backend before submitting an application or opening a portal. The public website can still be viewed without the API, but database-backed login, applications, documents, and assessments require the API and PostgreSQL.

Run the backend test in another terminal:

```powershell
Set-Location backend
.venv\Scripts\python.exe -m pytest
```

## 6. Start the frontend on a phone-friendly local server

Do not rely on opening the HTML as a `file://` URL once API calls are involved. From the repository root, run:

```powershell
py -m http.server 5500
```

Open `http://localhost:5500` on the development computer. For a phone on the same Wi-Fi network, find the computer's local IP with `ipconfig`, then open `http://YOUR-COMPUTER-IP:5500` on the phone. Ensure Windows Firewall permits the development port.

## 7. Build the full platform in safe increments

1. **Keep the public website stable.** Move the remaining inline styles into `frontend/css/site.css` and the remaining inline script into `frontend/js/site.js`. Test the menu, slider, application modal, assessment, and teacher portal after each move.
2. **Add school configuration.** Load a school by its `slug` from the `schools` table. Logo, motto, contact details, colors, and content should come from that school record or a controlled configuration file.
3. **Add authentication.** Create login and password-reset endpoints. Store only password hashes, never plaintext passwords. Use role checks for admin, teacher, parent, and learner.
4. **Applications are database-backed.** `POST /api/v1/applications` validates the form and stores the application plus document bytes in PostgreSQL.
5. **Assessments are database-backed.** The backend scores submitted answers against PostgreSQL question keys and stores the answers and result.
6. **Authentication is database-backed.** Login checks a PBKDF2 password hash in PostgreSQL and returns an expiring signed token. Every staff query is filtered by `school_id`.
7. **Add testing and deployment.** Test API permissions, form validation, mobile layouts, and database migrations. Deploy the frontend, API, and PostgreSQL with separate secrets and HTTPS.

## 8. Smartphone and low-bandwidth rules

- Use compressed WebP/JPEG images and meaningful `alt` text.
- Keep the public page mostly server-delivered HTML and CSS.
- Avoid large frontend frameworks until the platform genuinely needs one.
- Use pagination for applications and assessment records.
- Use clear touch targets, short forms, and server-side validation.
- Show useful loading and offline/error messages instead of silently failing.
- Never require a learner to download a large file for a simple result or announcement.

## 9. Reusing the platform for another school

Create a new row in `schools`, then associate users, applications, and assessments with that `school_id`. Every protected query must filter by the authenticated user's school. This prevents one school from seeing another school's records.

A future deployment can use one database with `school_id` on shared tables, which is simple and cost-efficient for many small schools. A larger school or stricter isolation requirement can later use a separate database or schema per school.

## 10. Free public deployment

GitHub Pages can host the public frontend for free, but it cannot run FastAPI or PostgreSQL. A free-tier deployment uses:

- GitHub Pages for `index.html` and `frontend/`.
- Render for the FastAPI service using the repository `render.yaml` file.
- Supabase or Neon for a hosted PostgreSQL database.

Free services may sleep when idle, have usage limits, and are not suitable for guaranteed school production traffic. Do not store real learner documents until hosting privacy controls, backups, and retention policies have been reviewed.

### Deployment order

1. Create a free PostgreSQL project with Supabase or Neon and copy its connection string.
2. Run `database/schema.sql` and `database/seed.sql` against that hosted database.
3. In GitHub, open **Settings > Pages**, choose **GitHub Actions** as the source, and push the repository. The workflow in `.github/workflows/pages.yml` publishes only the frontend files.
4. Create a Render web service from the GitHub repository. Render can use `render.yaml` to configure the Python service.
5. Add these Render environment variables:
	- `DATABASE_URL`: the hosted PostgreSQL connection string.
	- `SECRET_KEY`: a long random private value.
	- `CORS_ORIGINS`: the exact GitHub Pages origin, for example `https://philacoding.github.io`.
6. Copy the Render service URL, for example `https://siphesihle-school-api.onrender.com`.
7. Set `window.SCHOOL_API_URL` to `<render-url>/api/v1` before `frontend/js/api.js` loads in `index.html`, then push again.
8. Test health, student login, teacher login, applications, document uploads, assessments, and results from the GitHub Pages URL.
