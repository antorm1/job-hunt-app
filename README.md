# JobHunt App 🔍💼

> Real-time remote job aggregator from multiple public APIs

[![Python](https://img.shields.io/badge/Python-3.9+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![CI](https://img.shields.io/github/actions/workflow/status/antorm1/job-hunt-app/ci.yml?label=CI)](.github/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## Features

- 🌐 **Multi-source aggregation** — Remotive, Arbeitnow, RemoteOK
- 🔍 **Real-time search** — Filter by title, company, tags, or description
- 📂 **Category filtering** — Software dev, data science, AI/ML, design, etc.
- 🏷️ **Source badges** — See where each job was sourced from
- 🔖 **Save/bookmark jobs** — Persisted in localStorage
- 🌗 **Dark / Light theme** — Toggle with preference saved
- 📥 **Export to CSV** — Download filtered results
- 📋 **Job detail modal** — Click any card to view full details
- 📄 **Pagination** — Load more without refreshing
- 🔃 **Sorting** — By date, title, or company
- ⚡ **Backend caching** — 5-minute LRU cache to reduce API calls
- 🧪 **Test suite** — Unit tests for helpers and API endpoints
- 🚀 **CI pipeline** — Automated tests on push (Python 3.9–3.12)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| Frontend | Vanilla HTML/CSS/JS |
| HTTP | httpx (async) |
| Testing | pytest + pytest-asyncio |
| CI/CD | GitHub Actions |
| Styling | Custom CSS (dark + light themes) |
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

```bash
cd frontend
python -m http.server 3000
# Open http://localhost:3000
```

Or just open `frontend/index.html` directly in your browser.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/jobs` | Get aggregated jobs (with filters + pagination) |
| GET | `/api/jobs/export` | Export as CSV or JSON |
| GET | `/api/categories` | List available categories |
| GET | `/api/stats` | Live stats from all sources |
| GET | `/api/health` | Health check + version info |
| POST | `/api/cache/clear` | Clear the response cache |

### Query Parameters

```
GET /api/jobs?category=software-development&search=python&source=Remotive&sort=date&page=1&per_page=30
```

- `category` — Filter by job category
- `search` — Search in title, company, description, tags
- `source` — Filter by specific source
- `sort` — Sort by `date`, `title`, or `company`
- `page` — Page number (default: 1)
- `per_page` — Items per page (default: 30, max: 100)

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

## Job Sources

| Source | Auth | Coverage |
|--------|------|----------|
| [Remotive](https://remotive.com) | None | Remote jobs across categories |
| [Arbeitnow](https://arbeitnow.com) | None | Remote & EU jobs |
| [RemoteOK](https://remoteok.com) | None | Global remote jobs |

## Project Structure

```
job-hunt-app/
├── backend/
│   ├── main.py              # FastAPI server + aggregators + cache
│   └── requirements.txt     # Python dependencies
├── frontend/
│   └── index.html           # Single-page app (dark/light theme)
├── tests/
│   ├── __init__.py
│   └── test_main.py         # Unit + integration tests
├── .github/
│   └── workflows/
│       └── ci.yml           # CI pipeline (test + lint)
├── pyproject.toml           # Project metadata
├── LICENSE                  # MIT
└── README.md                # This file
```

## Running Tests

```bash
cd backend
pip install -r requirements.txt pytest pytest-asyncio
cd ../tests
python -m pytest -v
```

## License

MIT — see [LICENSE](LICENSE) for details.

Built by [Antorm](https://github.com/antorm1)
