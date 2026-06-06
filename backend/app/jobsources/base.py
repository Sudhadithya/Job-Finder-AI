from abc import ABC, abstractmethod
from datetime import datetime
from pydantic import BaseModel, Field

class JobPosting(BaseModel):
    job_id: str = Field(..., description="Unique identifier across all sources, e.g. linkedin:12345")
    role: str
    company: str
    location: str
    source: str
    url: str
    description: str
    posted_at: datetime = Field(default_factory=datetime.utcnow)

class BaseJobSource(ABC):
    @abstractmethod
    async def scrape(self) -> list[JobPosting]:
        """
        Scrape jobs from the source.
        Returns a list of JobPosting objects.
        """
        pass
