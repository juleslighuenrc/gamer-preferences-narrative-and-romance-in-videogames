Gamer Preferences: Narrative and Romance in Videogames

Dash Dashboard for Survey Responses (Anonymized & GitHub-safe)

📊 Project Overview

This project is a Dash interactive dashboard for visualizing survey responses about gamer preferences regarding:

Narrative depth in videogames

Romance options and relationship systems

Player identity and character choices

The dashboard is designed for:

Real-time or near real-time updates

Secure handling of credentials

Public publishing on GitHub without exposing sensitive data

All configuration files are anonymized and use environment variables to ensure safe deployment and sharing.

🎯 Research Purpose

This survey explores:

Whether narrative and romance options influence players’ game choices

How players engage with romance mechanics when available

Whether there is a relationship between:

Players’ personal identity and orientation

The identities and orientations they choose for in-game characters

The project aims to contribute to understanding:

Player motivation

Representation and identity in games

The role of romance and narrative in player experience

🔒 Ethics, Privacy & Anonymization

No personally identifying information (PII) is stored or displayed.

All credentials (database, Google Sheets, APIs) are handled via environment variables.

The repository contains only sanitized configuration files.

Real secrets are excluded using .gitignore.

This makes the repository safe for:

Public GitHub publishing

Academic or portfolio demonstration

Open-source sharing

⚠️ This repository does not include raw survey data or authentication credentials.

🧩 Features

Responsive multi-chart dashboard (no overlapping/smashed graphs)

Auto-refresh every 2 seconds for near real-time survey updates

Explicit dark color palette (avoids white/washed-out bars)

SQL-first architecture with automatic Google Sheets → SQL synchronization

Global typography styling:

Titles: Arial, 12, bold, black

Other text: Arial, 9, black

Environment-variable based secrets (no hardcoded passwords)

📁 Project Files

app.py – main Dash app to run locally or deploy

connecting.ipynb – notebook workflow (sanitized to use env vars)

requirements.txt – Python dependencies

.env.example – sample environment settings

.gitignore – excludes secrets and local artifacts

⚙️ Setup

Create and activate a virtual environment.

Install dependencies:

pip install -r requirements.txt


Create .env from .env.example and fill in your real values.

▶️ Run Dashboard
python app.py


Open:
http://127.0.0.1:8050/

🔄 Data Flow (Google Sheets + SQL)

Default mode: dashboard reads directly from Google Sheets (DASHBOARD_SOURCE=sheets).

SQL remains your database and is continuously updated from Google Sheets.

You can switch dashboard source to SQL at any time (DASHBOARD_SOURCE=sql).

On each cycle, the app syncs new Google Sheets rows into MySQL.

Set these variables in .env or Render:

DASHBOARD_SOURCE=sheets (recommended public mode)

GOOGLE_SHEET_NAME

GOOGLE_WORKSHEET_NAME (optional)

GOOGLE_SERVICE_ACCOUNT_JSON (recommended for cloud) or GOOGLE_CLIENT_SECRET_FILE (local)

SYNC_FROM_GOOGLE_SHEETS=true

SYNC_INTERVAL_SECONDS=2

🔐 Privacy / Security

Never commit .env or clientsecret.json.

Keep database and Google credentials in local/private files only.

Commit only .env.example for public use.

🏷 Repository Name Note

GitHub repository names cannot include :. Use this slug:

gamer-preferences-narrative-and-romance-in-videogames

Full display title (repo description):

Gamer Preferences: Narrative and Romance in Videogames

🚀 Push to GitHub

If this folder is not a git repo yet:

git init
git add .
git commit -m "Initial sanitized dashboard"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main


If it is already connected:

git add .
git commit -m "Sanitize secrets and add dashboard + docs"
git push

🌐 Deploy Online (Render)

This project is preconfigured for Render using render.yaml.

Option A: One-click Blueprint deploy
https://dashboard.render.com/blueprint/new?repo=https://github.com/juleslighuenrc/gamer-preferences-narrative-and-romance-in-videogames

Option B: Manual Render setup

Create a new Web Service from your GitHub repository.

Render will detect:

Build command: pip install -r requirements.txt

Start command: gunicorn app:server

Add environment variables in Render:

DB_HOST

DB_USER
