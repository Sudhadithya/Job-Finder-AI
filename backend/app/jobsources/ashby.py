import httpx
from datetime import datetime, timezone
from app.jobsources.base import BaseJobSource, JobPosting
from app.services.text_cleaner import clean_description

class AshbySource(BaseJobSource):
    def __init__(self, board_id: str, company_name: str,
                 aliases: list[str] | None = None,
                 exclude_terms: list[str] | None = None):
        self.board_id = board_id
        self.company_name = company_name
        self._aliases_lower = [a.lower() for a in aliases] if aliases else None
        self._exclude_lower = [t.lower() for t in exclude_terms] if exclude_terms else None

    def _title_passes(self, title_lower: str) -> bool:
        """Return True if the title passes alias inclusion and exclusion filters."""
        if self._exclude_lower:
            for term in self._exclude_lower:
                if term in title_lower:
                    return False
        if self._aliases_lower:
            return any(alias in title_lower for alias in self._aliases_lower)
        return True

    async def scrape(self) -> list[JobPosting]:
        url = f"https://api.ashbyhq.com/posting-api/job-board/{self.board_id}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                if response.status_code != 200:
                    print(f"Ashby API returned status {response.status_code} for {self.board_id}")
                    return []
                
                data = response.json()
                jobs = data.get("jobs", [])
                
                postings = []
                for j in jobs:
                    j_id = (j.get("id") or "").strip()
                    title = (j.get("title") or "").strip()
                    job_url = (j.get("jobUrl") or "").strip()

                    if not (j_id and title and job_url):
                        continue

                    # Early filter: alias inclusion + seniority exclusion
                    if not self._title_passes(title.lower()):
                        continue
                    
                    loc = (j.get("location") or "").strip()

                    # Ashby uses descriptionHtml — clean it
                    raw_html = j.get("descriptionHtml", "") or ""
                    description = clean_description(raw_html)

                    published_at_str = j.get("publishedAt")
                    
                    posted_at = datetime.now(timezone.utc)
                    if published_at_str:
                        try:
                            cleaned_dt = published_at_str.replace("Z", "+00:00")
                            posted_at = datetime.fromisoformat(cleaned_dt)
                        except Exception:
                            pass
                            
                    postings.append(JobPosting(
                        job_id=f"ashby:{self.board_id}:{j_id}",
                        role=title,
                        company=self.company_name,
                        location=loc,
                        source="ashby",
                        url=job_url,
                        description=description,
                        posted_at=posted_at
                    ))
                return postings
        except Exception as e:
            print(f"Error scraping Ashby board {self.board_id}: {e}")
            return []
