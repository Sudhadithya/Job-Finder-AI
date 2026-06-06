import httpx
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from app.jobsources.base import BaseJobSource, JobPosting

class YCJobSource(BaseJobSource):
    async def scrape(self) -> list[JobPosting]:
        url = "https://hnrss.org/jobs"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                if response.status_code != 200:
                    print(f"YC/HN jobs feed returned status {response.status_code}")
                    return []
                
                # Parse RSS XML
                root = ET.fromstring(response.content)
                channel = root.find("channel")
                if channel is None:
                    return []
                    
                items = channel.findall("item")
                postings = []
                
                for item in items:
                    title = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else ""
                    description = item.find("description").text if item.find("description") is not None else ""
                    pub_date_str = item.find("pubDate").text if item.find("pubDate") is not None else ""
                    
                    if not title or not link:
                        continue
                        
                    # Parse company and role from title
                    # E.g. "Figma (YC W13) is hiring software engineers"
                    # E.g. "Stripe hiring a Backend Developer"
                    match = re.search(r'(.*?)\s+(?:is\s+)?hiring\s+(?:for\s+)?(.*)', title, re.IGNORECASE)
                    if match:
                        company = match.group(1).strip()
                        role = match.group(2).strip()
                    else:
                        company = "Hacker News Startup"
                        role = title.strip()
                        
                    # Strip YC cohort info e.g. "Figma (YC W13)" -> "Figma"
                    company = re.sub(r'\s*\([^)]*YC[^)]*\)', '', company, flags=re.IGNORECASE).strip()
                    
                    # Try to extract location from description
                    # Many postings have "Location: Bangalore" or "Remote (US/India)"
                    loc = "Remote"
                    desc_lower = description.lower()
                    loc_match = re.search(r'location:\s*([^\n<]+)', description, re.IGNORECASE)
                    if loc_match:
                        loc = loc_match.group(1).strip()
                    else:
                        # Scan description for city names
                        if "bangalore" in desc_lower or "bengaluru" in desc_lower:
                            loc = "Bangalore, India"
                        elif "hyderabad" in desc_lower:
                            loc = "Hyderabad, India"
                        elif "india" in desc_lower and "remote" in desc_lower:
                            loc = "Remote, India"
                            
                    # Parse pubDate
                    posted_at = datetime.now(timezone.utc)
                    if pub_date_str:
                        try:
                            posted_at = parsedate_to_datetime(pub_date_str)
                        except Exception:
                            pass
                            
                    postings.append(JobPosting(
                        job_id=f"yc:{hash(link)}",
                        role=role,
                        company=company,
                        location=loc,
                        source="yc",
                        url=link,
                        description=description,
                        posted_at=posted_at
                    ))
                return postings
        except Exception as e:
            print(f"Error scraping YC/HN jobs feed: {e}")
            return []
