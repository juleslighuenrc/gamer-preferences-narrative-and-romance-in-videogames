# Gamer Preferences: Narrative and Romance in Videogames

Dash Dashboard for Survey Responses (Anonymized & GitHub-safe)

## Project Overview

This project is a Dash interactive dashboard for visualizing survey responses about gamer preferences regarding:
- Narrative depth in videogames
- Romance options and relationship systems
- Player identity and character choices

The dashboard is designed for:
- Real-time or near real-time updates
- Secure handling of credentials
- Public publishing on GitHub without exposing sensitive data

All configuration files are anonymized and use environment variables to ensure safe deployment and sharing.

## Research Purpose

This survey explores whether narrative and romance options influence players’ game choices, how players engage with romance mechanics when available
and whether there is a relationship between players’ personal identity and orientation and the ones they choose for in-game characters.
The goal is to know whether this relationship is strategically important when making decisions about development and story-line.

The project aims to contribute to understanding player motivation, representation, identiy and the role of romance and narrative in player experience.

## Ethics, Privacy & Anonymization

- No personally identifying information (PII) is stored or displayed.
- All credentials (database, Google Sheets, APIs) are handled via environment variables.
- The repository contains only sanitized configuration files.
- Real secrets are excluded using .gitignore.

This makes the repository safe for:
- Public GitHub publishing
- Academic or portfolio demonstration
- Open-source sharing

⚠️ This repository does not include raw survey data or authentication credentials.

## Features

- Responsive multi-chart dashboard (no overlapping/smashed graphs)
- Auto-refresh every 2 seconds for near real-time survey updates
- Explicit dark color palette (avoids white/washed-out bars)
- SQL-first architecture with automatic Google Sheets → SQL synchronization


# Project Files

app.py – main Dash app to run locally or deploy

connecting.ipynb – notebook workflow (sanitized to use env vars)

requirements.txt – Python dependencies

.env.example – sample environment settings

.gitignore – excludes secrets and local artifacts

 ## Setup Options

Create and activate a virtual environment.

Install dependencies:

pip install -r requirements.txt


Create .env from .env.example and fill in your real values.

▶️ Run Dashboard
python app.py


Open:
http://127.0.0.1:8050/

🔄 Data Flow (Google Sheets + SQL)

- Default mode: dashboard reads directly from Google Sheets (DASHBOARD_SOURCE=sheets).
- SQL remains database and is continuously updated from Google Sheets.
- It is possible to switch dashboard source to SQL at any time (DASHBOARD_SOURCE=sql).
- On each cycle, the app syncs new Google Sheets rows into MySQL.
