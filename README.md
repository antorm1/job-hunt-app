# JobHunt App 🔍💼

> Real-time remote job aggregator from multiple public APIs

[![Python](https://img.shields.io/badge/Python-3.9+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## Features

- 🌐 **Multi-source aggregation** — Remotive, Arbeitnow, RemoteOK
- 🔍 **Real-time search** — Filter by title, company, tags, or description
- 📂 **Category filtering** — Software dev, data science, AI/ML, design, etc.
- 🏷️ **Source badges** — See where each job was sourced from
- 📱 **Responsive** — Works on desktop and mobile
- ⚡ **Async API** — Fast concurrent fetching from all sources

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| Frontend | Vanilla HTML/CSS/JS |
| HTTP | httpx (async) |
| Styling | Custom CSS (dark theme) |
| Fonts | Inter (Google Fonts) |

## Quick Start

### 1. Start the backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

API runs at `http://localhost:8000`

### 2. Open the frontend

Open `frontend/index.html` in your browser, or serve it:

```bash
# Simple Python server
cd frontend
python -m http.server 3000
# Open http://localhost:3000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/jobs` | Get aggregated jobs (with filters) |
| GET | `/api/categories` | List available categories |
| GET | `/api/stats` | Live stats from all sources |
| GET | `/api/health` | Health check |

### Query Parameters

```
GET /api/jobs?category=software-development&search=python&source=Remotive
```

- `category` — Filter by job category
- `search` — Search in title, company, description, tags
- `source` — Filter by specific source

## Categories

- All Jobs
- Software Development
- Data Science
- Design
- Marketing
- DevOps
- AI / ML
- Data Annotation
- Customer Support

## Project Structure

```
job-hunt-app/
├── backend/
│   ├── main.py              # FastAPI server + job aggregators
│   └── requirements.txt     # Python dependencies
├── frontend/
│   └── index.html           # Single-page web app
├── pyproject.toml           # Project metadata
└── README.md                # This file
```

## Job Sources

| Source | Auth | Coverage |
|--------|------|----------|
| [Remotive](https://remotive.com) | None | Remote jobs across categories |
| [Arbeitnow](https://arbeitnow.com) | None | Remote & EU jobs |
| [RemoteOK](https://remoteok.com) | None | Global remote jobs |

## License

MIT — see [LICENSE](LICENSE) for details.

Built by [Antorm](https://github.com/antorm1)
