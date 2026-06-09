import httpx
from datetime import datetime, timezone
from app.jobsources.base import BaseJobSource, JobPosting
from app.services.text_cleaner import clean_description

class LeverSource(BaseJobSource):
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
        url = f"https://api.lever.co/v0/postings/{self.board_id}?mode=json"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                if response.status_code != 200:
                    print(f"Lever API returned status {response.status_code} for {self.board_id}")
                    return []
                
                jobs = response.json()
                postings = []
                for j in jobs:
                    j_id = j.get("id", "").strip()
                    title = (j.get("text") or "").strip()
                    hosted_url = (j.get("hostedUrl") or "").strip()

                    if not (j_id and title and hosted_url):
                        continue

                    # Early filter: alias inclusion + seniority exclusion
                    if not self._title_passes(title.lower()):
                        continue
                    
                    categories = j.get("categories", {})
                    loc = (categories.get("location") or "").strip()
                    
                    # Lever description is HTML; clean it
                    raw_description = j.get("description", "") or ""
                    clean_desc = clean_description(raw_description)

                    # Lever lists (Requirements, Responsibilities, etc.) are also HTML
                    lists = j.get("lists", [])
                    list_parts = []
                    for lst in lists:
                        section_title = (lst.get("text") or "").strip()
                        # lst["content"] is an HTML string with <li> items
                        raw_items = lst.get("content", "") or ""
                        cleaned_items = clean_description(raw_items)
                        if section_title:
                            list_parts.append(f"### {section_title}\n{cleaned_items}")
                        else:
                            list_parts.append(cleaned_items)

                    full_desc = clean_desc
                    if list_parts:
                        full_desc = clean_desc + "\n\n" + "\n\n".join(list_parts)
                    
                    created_at_ms = j.get("createdAt")
                    posted_at = datetime.now(timezone.utc)
                    if created_at_ms:
                        try:
                            posted_at = datetime.fromtimestamp(created_at_ms / 1000.0, tz=timezone.utc)
                        except Exception:
                            pass
                            
                    postings.append(JobPosting(
                        job_id=f"lever:{self.board_id}:{j_id}",
                        role=title,
                        company=self.company_name,
                        location=loc,
                        source="lever",
                        url=hosted_url,
                        description=full_desc,
                        posted_at=posted_at
                    ))
                return postings
        except Exception as e:
            print(f"Error scraping Lever board {self.board_id}: {e}")
            return []
