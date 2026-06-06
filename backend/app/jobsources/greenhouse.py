import httpx
from datetime import datetime, timezone
from app.jobsources.base import BaseJobSource, JobPosting
from app.services.text_cleaner import clean_description

class GreenhouseSource(BaseJobSource):
    def __init__(self, board_id: str, company_name: str):
        self.board_id = board_id
        self.company_name = company_name

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
                    
                    if not (j_id and title and abs_url):
                        continue
                    
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
