# Survey Narrative Dashboard

Dash dashboard for survey responses with anonymized configuration for safe GitHub publishing.

## Features

- Responsive multi-chart dashboard (no overlapping/smashed graphs)
- Auto-refresh every 2 seconds for near real-time survey updates
- Explicit dark color palette (avoids white/washed-out bars)
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
