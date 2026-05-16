"""Job Hunt App - Backend API that aggregates jobs from multiple public sources."""

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import asyncio
import hashlib
import json
import csv
import io

app = FastAPI(
    title="Job Hunt API",
    description="Aggregates remote jobs from multiple public APIs",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_TIMEOUT = 15

# ─── Simple in-memory cache ───
_cache: dict = {}
CACHE_TTL = 300  # 5 minutes


def cache_get(key: str) -> dict | None:
    entry = _cache.get(key)
    if entry and datetime.utcnow() < entry["expires"]:
        return entry["data"]
    _cache.pop(key, None)
    return None


def cache_set(key: str, data: dict):
    _cache[key] = {"data": data, "expires": datetime.utcnow() + timedelta(seconds=CACHE_TTL)}


def cache_clear():
    _cache.clear()


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
    page: int
    per_page: int
    has_more: bool


def _make_id(source: str, text: str) -> str:
    return hashlib.md5(f"{source}:{text}".encode()).hexdigest()[:12]


def _clean(text: str | None, max_len: int = 500) -> str:
    if not text:
        return ""
    t = text.strip()
    # Strip HTML tags
    while "<" in t and ">" in t:
        t = t[: t.index("<")] + t[t.index(">") + 1 :]
    t = t.replace("\n", " ").replace("\r", " ").replace("  ", " ")
    return t[:max_len] + ("…" if len(t) > max_len else "")


# ─── Job source: Remotive ───
async def fetch_remotive(category: str | None = None) -> list[Job]:
    url = "https://remotive.com/api/remote-jobs"
    params: dict = {"limit": 50}
    if category:
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
                            tags=[t for t in (j.get("tags") or []) if t][:6],
                            source="Remotive",
                            posted_date=j.get("publication_date", ""),
                            is_remote=True,
                        )
                    )
                return jobs
        except Exception:
            pass
    return []


# ─── Job source: Arbeitnow ───
async def fetch_arbeitnow() -> list[Job]:
    url = "https://arbeitnow.com/api/job-board-api"
    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        try:
            resp = await client.get(url, params={"limit": 50})
            if resp.status_code == 200:
                data = resp.json()
                jobs = []
                for j in data.get("data", []):
                    # Only include remote-ish jobs
                    tags = [t.lower() for t in (j.get("tags") or [])]
                    location = (j.get("location", "") or "").lower()
                    is_remote = "remote" in tags or "wfh" in tags or "remote" in location or "worldwide" in location
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
                            category=", ".join(j.get("job_types", []) or []),
                            description=_clean(desc),
                            url=j.get("url", "") or "",
                            salary=j.get("salary", "") or None,
                            tags=[t for t in (j.get("tags") or []) if t][:6],
                            source="Arbeitnow",
                            posted_date=str(j.get("created_at", ""))[:10] if j.get("created_at") else None,
                            is_remote=True,
                        )
                    )
                return jobs
        except Exception:
            pass
    return []


# ─── Job source: RemoteOK ───
async def fetch_remote_ok() -> list[Job]:
    url = "https://remoteok.com/api"
    headers = {"User-Agent": "JobHuntApp/1.0"}
    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                jobs = []
                for j in data[:60]:
                    if not isinstance(j, dict) or not j.get("id"):
                        continue
                    salary = ""
                    if j.get("salary_max") and j.get("salary_min"):
                        smin = j["salary_min"]
                        smax = j["salary_max"]
                        if smin and smax:
                            try:
                                salary = f"${int(smin/1000)}k-${int(smax/1000)}k"
                            except (ValueError, TypeError):
                                salary = str(j.get("salary", ""))
                        else:
                            salary = str(j.get("salary", ""))
                    else:
                        salary = str(j.get("salary", ""))

                    jobs.append(
                        Job(
                            id=_make_id("remoteok", str(j.get("id", ""))),
                            title=j.get("position", "") or "",
                            company=j.get("company", "") or "",
                            location=j.get("location", "") or "Remote",
                            category=j.get("job_type", "") or "",
                            description=_clean(j.get("description", "")),
                            url=j.get("url", "") or "",
                            salary=salary if salary and salary != "None" else None,
                            tags=[t for t in (j.get("tags") or []) if t][:6],
                            source="RemoteOK",
                            posted_date=str(j.get("date", "")),
                            is_remote=True,
                        )
                    )
                return jobs
        except Exception:
            pass
    return []


# ─── Job source: Remote.co ───
async def fetch_remoteco() -> list[Job]:
    """Fetch from remote.co job feed (RSS via alternative endpoint)."""
    url = "https://remote.co/remote-jobs/"
    # remote.co doesn't have a clean JSON API, so we simulate with a curated set
    # In production you'd use an RSS parser. For portfolio demo, we skip gracefully.
    return []


# ─── Job source: JustRemote ───
async def fetch_justremote() -> list[Job]:
    """JustRemote doesn't have a public JSON API — placeholder for future integration."""
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
    search: str = Query("", description="Search in title, company, description, tags"),
    source: str = Query("", description="Filter by source name"),
    sort: str = Query("date", description="Sort by: date, title, company"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(30, ge=1, le=100, description="Items per page"),
):
    """Fetch jobs from all available sources with filtering, sorting, and pagination."""

    cache_key = f"jobs:{category}:{search}:{source}:{sort}:{page}:{per_page}"
    cached = cache_get(cache_key)
    if cached:
        return JobsResponse(**cached)

    # Build fetchers
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
        key = f"{job.title.lower().strip()}|{job.company.lower().strip()}"
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    # Apply filters
    filtered = unique_jobs

    if search:
        s = search.lower()
        filtered = [
            j for j in filtered
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
            j for j in filtered
            if cat in j.category.lower()
            or cat in j.title.lower()
            or cat in j.description.lower()
            or any(cat in t.lower() for t in j.tags)
            or cat in j.source.lower()
        ]

    # Sort
    if sort == "title":
        filtered.sort(key=lambda j: j.title.lower())
    elif sort == "company":
        filtered.sort(key=lambda j: j.company.lower())
    else:  # date — keep API order (newest first)
        pass

    # Pagination
    total = len(filtered)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = filtered[start:end]
    has_more = end < total

    resp_data = {
        "jobs": paginated,
        "total": total,
        "sources": active_sources,
        "page": page,
        "per_page": per_page,
        "has_more": has_more,
    }

    cache_set(cache_key, resp_data)
    return JobsResponse(**resp_data)


@app.get("/api/jobs/export")
async def export_jobs(
    category: str = Query("all"),
    search: str = Query(""),
    source: str = Query(""),
    fmt: str = Query("csv", regex="^(csv|json)$"),
):
    """Export filtered jobs as CSV or JSON."""
    fetchers = [fetch_remotive(category if category != "all" else None), fetch_arbeitnow(), fetch_remote_ok()]
    results = await asyncio.gather(*fetchers, return_exceptions=True)

    all_jobs: list[Job] = []
    for result in results:
        if isinstance(result, list):
            all_jobs.extend(result)

    seen = set()
    unique = []
    for j in all_jobs:
        key = f"{j.title.lower().strip()}|{j.company.lower().strip()}"
        if key not in seen:
            seen.add(key)
            unique.append(j)

    filtered = unique
    if search:
        s = search.lower()
        filtered = [j for j in filtered if s in j.title.lower() or s in j.company.lower() or s in j.description.lower()]
    if source:
        filtered = [j for j in filtered if j.source.lower() == source.lower()]

    if fmt == "json":
        return JSONResponse(content={"jobs": [j.model_dump() for j in filtered], "total": len(filtered)})

    # CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Title", "Company", "Location", "Category", "Source", "Salary", "URL", "Tags", "Posted"])
    for j in filtered:
        writer.writerow([j.title, j.company, j.location, j.category, j.source, j.salary or "", j.url, ", ".join(j.tags), j.posted_date or ""])

    return JSONResponse(
        content={"message": "CSV ready"},
        headers={"Content-Disposition": f"attachment; filename=jobs_export_{datetime.utcnow().strftime('%Y%m%d')}.csv"},
    )


@app.get("/api/stats")
async def get_stats():
    """Quick stats from all sources."""
    fetchers = [fetch_remotive(), fetch_arbeitnow(), fetch_remote_ok()]
    results = await asyncio.gather(*fetchers, return_exceptions=True)

    stats = {"total": 0, "sources": {}, "cached": len(_cache)}
    source_names = ["Remotive", "Arbeitnow", "RemoteOK"]

    for i, result in enumerate(results):
        name = source_names[i]
        count = len(result) if isinstance(result, list) else 0
        stats["sources"][name] = count
        stats["total"] += count

    return stats


@app.post("/api/cache/clear")
async def clear_cache():
    """Clear the API cache."""
    cache_clear()
    return {"status": "cache cleared"}


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.1.0",
        "cache_entries": len(_cache),
        "uptime_check": True,
    }
