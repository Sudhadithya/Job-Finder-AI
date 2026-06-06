import json
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from app.jobsources.base import BaseJobSource, JobPosting

class CompanyCareersSource(BaseJobSource):
    def __init__(self, company_name: str, url: str):
        self.company_name = company_name
        self.url = url

    async def scrape(self) -> list[JobPosting]:
        try:
            async with httpx.AsyncClient() as client:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                response = await client.get(self.url, timeout=10.0, headers=headers)
                if response.status_code != 200:
                    return []
                
                soup = BeautifulSoup(response.text, "html.parser")
                ld_json_scripts = soup.find_all("script", type="application/ld+json")
                
                postings = []
                for idx, script in enumerate(ld_json_scripts):
                    if not script.string:
                        continue
                    try:
                        data = json.loads(script.string.strip())
                        graphs = []
                        if isinstance(data, list):
                            graphs = data
                        elif isinstance(data, dict):
                            if data.get("@type") == "JobPosting":
                                graphs = [data]
                            elif "@graph" in data:
                                graphs = data["@graph"]
                                
                        for graph in graphs:
                            if isinstance(graph, dict) and graph.get("@type") == "JobPosting":
                                title = graph.get("title")
                                desc = graph.get("description", "")
                                date_posted_str = graph.get("datePosted")
                                
                                # Parse location
                                loc = ""
                                job_loc = graph.get("jobLocation", {})
                                if isinstance(job_loc, dict):
                                    address = job_loc.get("address", {})
                                    if isinstance(address, dict):
                                        loc_parts = []
                                        if address.get("addressLocality"):
                                            loc_parts.append(str(address.get("addressLocality")))
                                        if address.get("addressRegion"):
                                            loc_parts.append(str(address.get("addressRegion")))
                                        if address.get("addressCountry"):
                                            loc_parts.append(str(address.get("addressCountry")))
                                        loc = ", ".join(loc_parts)
                                
                                posted_at = datetime.now(timezone.utc)
                                if date_posted_str:
                                    try:
                                        posted_at = datetime.fromisoformat(date_posted_str.replace("Z", "+00:00"))
                                    except Exception:
                                        pass
                                        
                                if title:
                                    postings.append(JobPosting(
                                        job_id=f"careers:{self.company_name}:{idx}",
                                        role=title,
                                        company=self.company_name,
                                        location=loc or "Remote",
                                        source="careers",
                                        url=self.url,
                                        description=desc,
                                        posted_at=posted_at
                                    ))
                    except Exception:
                        pass
                return postings
        except Exception as e:
            print(f"Error scraping company career page for {self.company_name}: {e}")
            return []
