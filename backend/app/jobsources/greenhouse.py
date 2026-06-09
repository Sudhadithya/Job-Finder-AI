import httpx
from datetime import datetime, timezone
from app.jobsources.base import BaseJobSource, JobPosting
from app.services.text_cleaner import clean_description

class GreenhouseSource(BaseJobSource):
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
        url = f"https://boards-api.greenhouse.io/v1/boards/{self.board_id}/jobs?content=true"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                if response.status_code != 200:
                    print(f"Greenhouse API returned status {response.status_code} for {self.board_id}")
                    return []
                
                data = response.json()
                jobs = data.get("jobs", [])
                
                postings = []
                for j in jobs:
                    j_id = j.get("id")
                    title = j.get("title", "").strip()
                    abs_url = j.get("absolute_url", "").strip()
                    
                    if not (j_id and title and abs_url):
                        continue

                    # Early filter: alias inclusion + seniority exclusion
                    if not self._title_passes(title.lower()):
                        continue

                    loc_data = j.get("location")
                    loc = loc_data.get("name", "").strip() if loc_data else ""
                    
                    # Clean HTML description before storing
                    raw_content = j.get("content", "") or ""
                    content = clean_description(raw_content)
                    
                    updated_at_str = j.get("updated_at")
                    
                    # Convert posted_at
                    posted_at = datetime.now(timezone.utc)
                    if updated_at_str:
                        try:
                            cleaned_dt = updated_at_str.replace("Z", "+00:00")
                            posted_at = datetime.fromisoformat(cleaned_dt)
                        except Exception:
                            pass
                    
                    postings.append(JobPosting(
                        job_id=f"greenhouse:{self.board_id}:{j_id}",
                        role=title,
                        company=self.company_name,
                        location=loc,
                        source="greenhouse",
                        url=abs_url,
                        description=content,
                        posted_at=posted_at
                    ))
                return postings
        except Exception as e:
            print(f"Error scraping Greenhouse board {self.board_id}: {e}")
            return []
