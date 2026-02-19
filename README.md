# Survey Narrative Dashboard

Dash dashboard for survey responses with anonymized configuration for safe GitHub publishing.

## Features

- Responsive multi-chart dashboard (no overlapping/smashed graphs)
- Auto-refresh every 2 seconds for near real-time survey updates
- Explicit dark color palette (avoids white/washed-out bars)
- SQL-first architecture with automatic Google Sheets -> SQL synchronization
- Global typography styling:
  - Titles: Arial, 12, bold, black
  - Other text: Arial, 9, black
- Environment-variable based secrets (no hardcoded passwords)

## Project Files

- `app.py` - main Dash app to run locally or deploy
- `connecting.ipynb` - notebook workflow (sanitized to use env vars)
- `requirements.txt` - Python dependencies
- `.env.example` - sample environment settings
- `.gitignore` - excludes secrets and local artifacts

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create `.env` from `.env.example` and fill your real values.

## Run Dashboard

```bash
python app.py
```

Open: `http://127.0.0.1:8050/`

## Data Flow (Google Sheets + SQL)

- The dashboard always reads from `survey_responses` in MySQL.
- On each cycle, the app syncs new Google Sheets rows into MySQL.
- Set these variables in `.env` or Render:
  - `GOOGLE_SHEET_NAME`
  - `GOOGLE_WORKSHEET_NAME` (optional)
  - `GOOGLE_SERVICE_ACCOUNT_JSON` (recommended for cloud) or `GOOGLE_CLIENT_SECRET_FILE` (local)
  - `SYNC_FROM_GOOGLE_SHEETS=true`
  - `SYNC_INTERVAL_SECONDS=2`

## Privacy / Security

- Never commit `.env` or `clientsecret.json`.
- Keep your database credentials and Google credentials only in local/private files.
- Keep your repository Public-safe by committing only `.env.example` and never real secrets.

## Repository Name Note

GitHub repository names cannot include `:`. Use this slug:

- `gamer-preferences-narrative-and-romance-in-videogames`

Then set the full title in the repo description:

- `Gamer Preferences: Narrative and Romance in Videogames`

## Push to GitHub

If this folder is not a git repo yet:

```bash
git init
git add .
git commit -m "Initial sanitized dashboard"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

If it is already connected to a remote:

```bash
git add .
git commit -m "Sanitize secrets and add dashboard + docs"
git push
```

### One-command private publish (recommended)

After authenticating with GitHub CLI:

```powershell
gh auth login --web
powershell -ExecutionPolicy Bypass -File .\publish_to_github.ps1
```

## Deploy Online (Render)

This project is preconfigured for Render using `render.yaml`.

### Option A: One-click Blueprint deploy

Use this URL (while logged into Render):

- `https://dashboard.render.com/blueprint/new?repo=https://github.com/juleslighuenrc/gamer-preferences-narrative-and-romance-in-videogames`

### Option B: Manual Render setup

1. In Render, create a new **Web Service** from your GitHub repository.
2. Render will detect:
  - Build command: `pip install -r requirements.txt`
  - Start command: `gunicorn app:server`
3. Add environment variables in Render:
  - `DB_HOST`
  - `DB_USER`
  - `DB_PASSWORD`
  - `DB_NAME`
  - `DASH_DEBUG=false`
4. Deploy and open the generated Render URL.
