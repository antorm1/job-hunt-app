"""Job Hunt App - Backend API that aggregates jobs from multiple public sources."""

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import asyncio
import hashlib

app = FastAPI(
    title="Job Hunt API",
    description="Aggregates remote jobs from multiple public APIs",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_TIMEOUT = 15  # seconds


class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str
    category: str
    description: str
    url: str
    salary: Optional[str] = None
    tags: list[str] = []
    source: str
    posted_date: Optional[str] = None
    is_remote: bool = True


class JobsResponse(BaseModel):
    jobs: list[Job]
    total: int
    sources: list[str]


def _make_id(source: str, text: str) -> str:
    return hashlib.md5(f"{source}:{text}".encode()).hexdigest()[:12]


def _clean(text: str | None, max_len: int = 300) -> str:
    if not text:
        return ""
    t = text.strip().replace("\n", " ").replace("\r", "")
    return t[:max_len] + ("..." if len(t) > max_len else "")


async def fetch_remotive(category: str | None = None) -> list[Job]:
    """Fetch from Remotive API (free, no auth)."""
    url = "https://remotive.com/api/remote-jobs"
    params: dict = {"limit": 50}
    if category:
        # Remotive uses specific category slugs
        slug_map = {
            "software-dev": "software-development",
            "data": "data-science",
            "design": "design",
            "marketing": "marketing",
            "sales": "sales",
            "support": "customer-support",
            "hr": "hr",
            "finance": "finance",
            "devops": "devops",
        }
        params["category"] = slug_map.get(category, category)

    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        try:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                jobs = []
                for j in data.get("jobs", []):
                    jobs.append(
                        Job(
                            id=_make_id("remotive", str(j.get("id", ""))),
                            title=j.get("title", "") or "",
                            company=j.get("company_name", "") or "",
                            location=j.get("candidate_required_location", "") or "Remote",
                            category=j.get("category", "") or "",
                            description=_clean(j.get("description", "")),
                            url=j.get("url", "") or "",
                            tags=j.get("tags", []) or [],
                            source="Remotive",
                            posted_date=j.get("publication_date", ""),
                            is_remote=True,
                        )
                    )
                return jobs
        except Exception:
            pass
    return []


async def fetch_arbeitnow(remote_only: bool = True) -> list[Job]:
    """Fetch from Arbeitnow API (free, no auth)."""
    url = "https://arbeithub.com/api/jobs"
    # Use the actual arbeitnow API
    url = "https://arbeitnow.com/api/job-board-api"

    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                jobs = []
                for j in data.get("data", []):
                    # Skip if we only want remote and job isn't remote
                    if remote_only:
                        tags = j.get("tags", []) or []
                        location = (j.get("location", "") or "").lower()
                        is_remote = "remote" in tags or "wfh" in tags or "remote" in location
                        if not is_remote:
                            continue

                    desc = ""
                    if isinstance(j.get("description"), str):
                        desc = j["description"]
                    elif isinstance(j.get("description"), dict):
                        desc = j["description"].get("html", j["description"].get("text", ""))

                    jobs.append(
                        Job(
                            id=_make_id("arbeitnow", str(j.get("slug", ""))),
                            title=j.get("title", "") or "",
                            company=j.get("company_name", "") or "",
                            location=j.get("location", "") or "Remote",
                            category=j.get("job_types", []) or [],
                            description=_clean(desc),
                            url=j.get("url", "") or "",
                            salary=j.get("salary", "") or None,
                            tags=j.get("tags", []) or [],
                            source="Arbeitnow",
                            posted_date=str(j.get("created_at", ""))[:10]
                            if j.get("created_at")
                            else None,
                            is_remote=True,
                        )
                    )
                return jobs
        except Exception:
            pass
    return []


async def fetch_python_dev_jobs() -> list[Job]:
    """Fetch from Python Developer Jobs (free, no auth)."""
    url = "https://pythonjob.com/api/jobs"

    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                jobs = []
                for j in data.get("jobs", [])[:50]:
                    jobs.append(
                        Job(
                            id=_make_id("pythonjob", str(j.get("id", ""))),
                            title=j.get("title", "") or "",
                            company=j.get("company", "") or "",
                            location=j.get("location", "") or "Remote",
                            category="Software Development",
                            description=_clean(j.get("description", "")),
                            url=j.get("apply", j.get("url", "")) or "",
                            tags=j.get("tags", []) or [],
                            source="Python Jobs",
                            posted_date=j.get("date", ""),
                            is_remote=True,
                        )
                    )
                return jobs
        except Exception:
            pass
    return []


async def fetch_remote_ok() -> list[Job]:
    """Fetch from RemoteOK API."""
    url = "https://remoteok.com/api"
    headers = {"User-Agent": "JobHuntApp/1.0"}

    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                jobs = []
                for j in data[:50]:
                    if not isinstance(j, dict):
                        continue
                    jobs.append(
                        Job(
                            id=_make_id("remoteok", str(j.get("id", ""))),
                            title=j.get("position", "") or "",
                            company=j.get("company", "") or "",
                            location=j.get("location", "") or "Remote",
                            category=j.get("job_type", "") or "",
                            description=_clean(j.get("description", "")),
                            url=j.get("url", "") or "",
                            salary=j.get("salary", j.get("salary_max", "")) or None,
                            tags=j.get("tags", []) or [],
                            source="RemoteOK",
                            posted_date=j.get("date", ""),
                            is_remote=True,
                        )
                    )
                return jobs
        except Exception:
            pass
    return []


CATEGORIES = [
    "all",
    "software-development",
    "data-science",
    "design",
    "marketing",
    "sales",
    "customer-support",
    "devops",
    "content-writing",
    "ai-ml",
    "data-annotation",
]


@app.get("/api/categories")
async def get_categories():
    return {"categories": CATEGORIES}


@app.get("/api/jobs", response_model=JobsResponse)
async def get_jobs(
    category: str = Query("all", description="Job category filter"),
    search: str = Query("", description="Search in title and description"),
    source: str = Query("", description="Filter by source (e.g. Remotive, Arbeitnow)"),
):
    """Fetch jobs from all available sources with optional filtering."""

    # Build fetchers list
    fetchers = [
        fetch_remotive(category if category != "all" else None),
        fetch_arbeitnow(),
        fetch_remote_ok(),
    ]

    results = await asyncio.gather(*fetchers, return_exceptions=True)

    all_jobs: list[Job] = []
    active_sources: list[str] = []

    source_names = ["Remotive", "Arbeitnow", "RemoteOK"]
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            continue
        if result:
            all_jobs.extend(result)
            if source_names[i] not in active_sources:
                active_sources.append(source_names[i])

    # Deduplicate by title + company
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = f"{job.title.lower()}|{job.company.lower()}"
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    # Apply filters
    filtered = unique_jobs

    if search:
        s = search.lower()
        filtered = [
            j
            for j in filtered
            if s in j.title.lower()
            or s in j.company.lower()
            or s in j.description.lower()
            or any(s in t.lower() for t in j.tags)
        ]

    if source:
        filtered = [j for j in filtered if j.source.lower() == source.lower()]

    if category != "all":
        cat = category.lower()
        filtered = [
            j
            for j in filtered
            if cat in j.category.lower()
            or cat in j.title.lower()
            or cat in j.description.lower()
            or any(cat in t.lower() for t in j.tags)
        ]

    return JobsResponse(jobs=filtered, total=len(filtered), sources=active_sources)


@app.get("/api/stats")
async def get_stats():
    """Quick stats from all sources."""
    fetchers = [fetch_remotive(), fetch_arbeitnow(), fetch_remote_ok()]
    results = await asyncio.gather(*fetchers, return_exceptions=True)

    stats = {"total": 0, "sources": {}}
    source_names = ["Remotive", "Arbeitnow", "RemoteOK"]

    for i, result in enumerate(results):
        name = source_names[i]
        count = len(result) if isinstance(result, list) else 0
        stats["sources"][name] = count
        stats["total"] += count

    return stats


@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
