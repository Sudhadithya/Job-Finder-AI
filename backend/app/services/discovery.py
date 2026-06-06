"""
discovery.py — Job discovery pipeline (v2).

Phases:
  1. Scrape verified ATS boards (Greenhouse / Lever / Ashby)
  2. Optional: probe custom career portals (Microsoft, Google, etc.) — skipped on failure
  3. Filter by role (SDE-1 / Data Scientist) using role_filter
  4. Filter by location (Bangalore / Hyderabad / Remote India)
  5. Filter by freshness (15 days)
  6. Validation gate (all required fields must exist)
  7. LLM extraction of structured fields (post-fetch)
  8. Store new jobs, skip duplicates
"""
import re
import json
import httpx
import asyncio
import time
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Job, DiscoveredCompany
from app.services.location import classify_location
from app.services.role_filter import classify_role, verdict_to_score_adjustment
from app.services.text_cleaner import clean_description
from app.jobsources.greenhouse import GreenhouseSource
from app.jobsources.lever import LeverSource
from app.jobsources.ashby import AshbySource

GEMINI_MODEL = "gemini-2.5-flash"

# ---------------------------------------------------------------------------
# Verified seed list — India-relevant companies.
# All slugs confirmed live via ATS API calls (2026-06-06).
#
# Live confirmed:
#   Greenhouse: postman, phonepe, groww, rubrik, databricks
#   Lever:      atlassian (0 jobs live), meesho, freshworks (0 jobs live)
#   Ashby:      confluent
#
# 404 / no standard ATS found (skipped):
#   Nutanix, Uber, Adobe, ServiceNow, BrowserStack, Razorpay,
#   Microsoft, Google, Amazon, Salesforce
# ---------------------------------------------------------------------------
SEED_COMPANIES = [
    # --- Greenhouse boards ---
    {"name": "Postman",    "board_type": "greenhouse", "board_id": "postman"},
    {"name": "PhonePe",    "board_type": "greenhouse", "board_id": "phonepe"},
    {"name": "Groww",      "board_type": "greenhouse", "board_id": "groww"},
    {"name": "Rubrik",     "board_type": "greenhouse", "board_id": "rubrik"},
    {"name": "Databricks", "board_type": "greenhouse", "board_id": "databricks"},

    # --- Lever boards ---
    {"name": "Atlassian",  "board_type": "lever", "board_id": "atlassian"},
    {"name": "Meesho",     "board_type": "lever", "board_id": "meesho"},
    {"name": "Freshworks", "board_type": "lever", "board_id": "freshworks"},

    # --- Ashby boards ---
    {"name": "Confluent",  "board_type": "ashby", "board_id": "confluent"},
]


def seed_companies_if_empty(db: Session):
    """
    Seed initial list of company job boards if the discovered_companies table is empty.
    """
    if db.query(DiscoveredCompany).count() == 0:
        print("Seeding initial company boards into database...")
        for c in SEED_COMPANIES:
            comp = DiscoveredCompany(
                name=c["name"],
                board_type=c["board_type"],
                board_id=c["board_id"]
            )
            db.add(comp)
        db.commit()


# ---------------------------------------------------------------------------
# LLM extraction (Phase 5)
# ---------------------------------------------------------------------------
def _fallback_extract(description: str) -> dict:
    """Rule-based fallback when LLM is unavailable."""
    lines = [l.strip() for l in description.split("\n") if l.strip()]

    required_skills = []
    preferred_skills = []
    is_pref = False

    for line in lines:
        line_lower = line.lower()

        # Skip markdown headings (### About Us, ### Requirements, etc.)
        if line.startswith("#"):
            continue

        if any(w in line_lower for w in ["preferred", "plus", "nice to have", "desired", "bonus"]):
            is_pref = True
        elif any(w in line_lower for w in ["required", "requirement", "qualification", "must have", "basic", "minimum"]):
            is_pref = False

        # Only pick up bullet-point items as skills (not prose sentences)
        if line.startswith(("-", "•")):
            cleaned = line.lstrip("-• ").strip()
            # Skip if too short, too long (prose), or looks like a heading
            if cleaned and 8 < len(cleaned) < 120:
                if is_pref:
                    if cleaned not in preferred_skills:
                        preferred_skills.append(cleaned)
                else:
                    if cleaned not in required_skills:
                        required_skills.append(cleaned)

    return {
        "role_type": "",
        "required_skills": required_skills[:6],
        "preferred_skills": preferred_skills[:6],
        "years_experience": "",
        "location": "",
        "employment_type": "",
    }


# Limit concurrent Gemini calls in discovery to 3 to avoid rate-limit exhaustion
# (reserve quota for resume parsing which is higher priority)
_GEMINI_SEMAPHORE = asyncio.Semaphore(3)

async def extract_job_fields(description: str) -> dict:
    """
    Extract structured fields from a job description.
    Uses rule-based fallback only — Gemini LLM is intentionally skipped here
    to preserve API quota for resume parsing (higher priority user-facing feature).
    """
    return _fallback_extract(description)


    prompt = f"""You are a technical recruiter. Analyze the job description below and extract:

Job Description:
{description[:4000]}

Return a JSON object with EXACTLY these keys:
{{
  "role_type": "one of: SDE-1, SDE-2, Senior SDE, Data Scientist, ML Engineer, DevOps, QA, Other",
  "required_skills": ["list of required skills/tech (max 8, each under 5 words)"],
  "preferred_skills": ["list of preferred/bonus skills (max 6, each under 5 words)"],
  "years_experience": "e.g. '0-2 years' or 'fresh graduate' or ''",
  "location": "city or 'Remote' or 'Hybrid' as mentioned in the job",
  "employment_type": "Full-time or Intern or Contract"
}}
Respond ONLY with a valid JSON object. No markdown, no extra text."""

    async with _GEMINI_SEMAPHORE:
        for attempt in range(3):
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={gemini_key}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json"}
                }
                async with httpx.AsyncClient() as client:
                    res = await client.post(url, headers=headers, json=payload, timeout=30.0)
                    if res.status_code == 429:
                        wait = 2 * (2 ** attempt)
                        print(f"Discovery LLM 429 rate limit -- retrying in {wait}s")
                        await asyncio.sleep(wait)
                        continue
                    res.raise_for_status()
                    data = res.json()
                    content = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if content.startswith("```"):
                        content = re.sub(r'^```[a-z]*\n?', '', content)
                        content = re.sub(r'\n?```$', '', content)
                    content = content.strip()
                    return json.loads(content)
            except Exception as e:
                if "429" not in str(e):
                    print(f"LLM extraction failed, using fallback: {e}")
                    return _fallback_extract(description)
                wait = 2 * (2 ** attempt)
                print(f"LLM extraction 429 retry {attempt+1}/3 in {wait}s")
                await asyncio.sleep(wait)

    return _fallback_extract(description)


# ---------------------------------------------------------------------------
# Validation gate (Phase 6)
# ---------------------------------------------------------------------------
def _is_valid_url(url: str) -> bool:
    return bool(url and url.startswith(("http://", "https://")))


def validate_posting(role: str, company: str, description: str, location: str, url: str) -> tuple[bool, str]:
    """
    Returns (is_valid, rejection_reason).
    A job must have all five fields present and non-trivial.
    """
    if not _is_valid_url(url):
        return False, "missing_or_invalid_url"
    if not role or not role.strip():
        return False, "missing_title"
    if not company or not company.strip():
        return False, "missing_company"
    if not location or not location.strip():
        return False, "missing_location"
    if not description or len(description.strip()) < 100:
        return False, "description_too_short"
    return True, ""


# ---------------------------------------------------------------------------
# Discovery pipeline
# ---------------------------------------------------------------------------
async def run_job_discovery(db: Session, user_category: str | None = None) -> dict:
    """
    Execute the full job discovery pipeline.

    Args:
        db:             SQLAlchemy session
        user_category:  The user's selected role category (e.g. "SDE-1")
                        Used for role filtering. If None, no role filter applied.

    Returns:
        Phase-7 report dict.
    """
    seed_companies_if_empty(db)

    # -----------------------------------------------------------------------
    # Phase 2: Load and validate boards
    # -----------------------------------------------------------------------
    companies = db.query(DiscoveredCompany).all()
    companies_checked = len(companies)

    # Skip recently failed boards (failed in last 24 h)
    skip_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    scrapers = []
    boards_skipped = 0
    for c in companies:
        if c.last_failed_at is not None:
            last_failed = c.last_failed_at
            if last_failed.tzinfo is None:
                last_failed = last_failed.replace(tzinfo=timezone.utc)
            if last_failed > skip_cutoff:
                print(f"  Skipping recently failed board: {c.name} ({c.board_type}/{c.board_id})")
                boards_skipped += 1
                continue

        if c.board_type == "greenhouse":
            scrapers.append((c, GreenhouseSource(c.board_id, c.name)))
        elif c.board_type == "lever":
            scrapers.append((c, LeverSource(c.board_id, c.name)))
        elif c.board_type == "ashby":
            scrapers.append((c, AshbySource(c.board_id, c.name)))

    print(f"Scraping {len(scrapers)} active company boards (skipped {boards_skipped} recently failed)...")

    SKIP_STATUS_CODES = {404, 403, 410}

    async def safe_scrape(c_entity, scraper):
        try:
            postings = await scraper.scrape()
            return postings, True, ""
        except Exception as e:
            reason = str(e)
            status_match = re.search(r'(\d{3})', reason)
            if status_match and int(status_match.group(1)) in SKIP_STATUS_CODES:
                reason = f"HTTP_{status_match.group(1)}"
            print(f"  Board scrape failed: {c_entity.name} — {reason}")
            return [], False, reason

    tasks = [safe_scrape(c_entity, scraper) for c_entity, scraper in scrapers]
    results = await asyncio.gather(*tasks)

    # Tally board-level results
    boards_successful = 0
    boards_failed = 0
    board_failures = []
    all_postings = []
    jobs_discovered = 0

    now = datetime.now(timezone.utc)
    for (c_entity, scraper), (postings, success, reason) in zip(scrapers, results):
        if success:
            boards_successful += 1
            if c_entity.last_failed_at is not None:
                c_entity.last_failed_at = None
        else:
            boards_failed += 1
            c_entity.last_failed_at = now
            board_failures.append({
                "company": c_entity.name,
                "board_type": c_entity.board_type,
                "board_id": c_entity.board_id,
                "reason": reason or "unknown"
            })
        all_postings.extend(postings)
        jobs_discovered += len(postings)

    db.commit()

    active_boards_found = boards_successful
    print(f"Board scraping complete: {boards_successful} OK, {boards_failed} failed.")

    for failure in board_failures:
        print(f"  BOARD_FAIL: {json.dumps(failure)}")

    # -----------------------------------------------------------------------
    # Phase 3–7: Filter, validate, extract, store
    # -----------------------------------------------------------------------
    fifteen_days_ago = now - timedelta(days=15)

    jobs_after_role_filter = 0
    jobs_after_location_filter = 0
    jobs_discarded_validation = 0
    jobs_duplicate_skipped = 0
    jobs_recommended = 0

    for p in all_postings:
        # --- Phase 3: Role filter ---
        verdict = classify_role(p.role, user_category)
        if verdict == "EXCLUDED":
            continue
        jobs_after_role_filter += 1

        # --- Phase 4: Location filter ---
        loc_class = classify_location(p.location)
        if loc_class not in ["BANGALORE", "HYDERABAD", "REMOTE_INDIA"]:
            continue
        jobs_after_location_filter += 1

        # --- Freshness filter (15 days) ---
        p_date = p.posted_at
        if p_date and p_date.tzinfo is None:
            p_date = p_date.replace(tzinfo=timezone.utc)
        if p_date and p_date < fifteen_days_ago:
            continue

        # --- Phase 6: Validation gate ---
        is_valid, rejection_reason = validate_posting(
            role=p.role,
            company=p.company,
            description=p.description,
            location=p.location,
            url=p.url,
        )
        if not is_valid:
            jobs_discarded_validation += 1
            print(f"  DISCARD [{rejection_reason}]: {p.company} — {p.role}")
            continue

        # --- Deduplication ---
        existing = db.query(Job).filter_by(job_id=p.job_id).first()
        if existing:
            jobs_duplicate_skipped += 1
            continue

        # --- Phase 5: LLM extraction ---
        extracted = await extract_job_fields(p.description)

        # Store the job
        db_job = Job(
            job_id=p.job_id,
            role=p.role,
            company=p.company,
            location=p.location,
            source=p.source,
            job_url=p.url,
            description=p.description,
            posted_at=p.posted_at,
            min_requirements=extracted.get("required_skills", []),
            preferred_requirements=extracted.get("preferred_skills", []),
        )
        db.add(db_job)
        jobs_recommended += 1

    db.commit()

    # -----------------------------------------------------------------------
    # Phase 7: Report
    # -----------------------------------------------------------------------
    report = {
        "companies_checked": companies_checked,
        "active_boards_found": active_boards_found,
        "jobs_discovered": jobs_discovered,
        "jobs_after_role_filter": jobs_after_role_filter,
        "jobs_after_location_filter": jobs_after_location_filter,
        "jobs_recommended": jobs_recommended,
        # Internal diagnostics (not in Phase-7 spec but helpful)
        "_boards_attempted": len(scrapers),
        "_boards_successful": boards_successful,
        "_boards_failed": boards_failed,
        "_board_failures": board_failures,
        "_jobs_discarded_validation": jobs_discarded_validation,
        "_jobs_duplicate_skipped": jobs_duplicate_skipped,
    }

    print(
        f"Discovery complete: {jobs_recommended} jobs stored. "
        f"Discovered={jobs_discovered} -> RoleFilter={jobs_after_role_filter} "
        f"-> LocationFilter={jobs_after_location_filter} -> Stored={jobs_recommended}"
    )
    return report
