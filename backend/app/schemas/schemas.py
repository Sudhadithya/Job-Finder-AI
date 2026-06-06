from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional

class UserUpdateCategory(BaseModel):
    category: str

class UserProfileResponse(BaseModel):
    id: UUID
    email: str
    desired_category: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ProjectResponse(BaseModel):
    name: str
    technologies: List[str]
    description: str
    highlights: List[str]

class ExperienceResponse(BaseModel):
    company: str
    role: str
    start_date: str
    end_date: str
    duration_months: int
    description: str
    technologies: List[str]
    highlights: List[str]

class ExtractionMetrics(BaseModel):
    projects_detected: int
    projects_extracted: int
    experience_detected: int
    experience_extracted: int
    skills_extracted: int

class ResumeUploadResponse(BaseModel):
    resume_id: UUID
    skills: List[str]
    projects: List[ProjectResponse]
    experience: List[ExperienceResponse]
    education: List[str]
    metrics: Optional[ExtractionMetrics] = None


class MatchRecommendationResponse(BaseModel):
    id: UUID
    user_id: UUID
    job_id: str
    score: int
    matching_skills: List[str]
    missing_skills: List[str]
    reasoning: str
    created_at: datetime
    company: str
    role: str
    job_url: str

    class Config:
        from_attributes = True

class BoardFailure(BaseModel):
    company: str
    board_type: str
    board_id: str
    reason: str

class DiscoverJobsResponse(BaseModel):
    """Phase-7 discovery report."""
    companies_checked: int = 0
    active_boards_found: int = 0
    jobs_discovered: int = 0
    jobs_after_role_filter: int = 0
    jobs_after_location_filter: int = 0
    jobs_recommended: int = 0
    # Kept for internal diagnostics / backwards compatibility
    new_jobs_found: int = 0
    boards_attempted: int = 0
    boards_successful: int = 0
    boards_failed: int = 0
    board_failures: List[BoardFailure] = []

class JobResponse(BaseModel):
    job_id: str
    role: str
    company: str
    location: str
    source: str
    job_url: str
    description: str
    posted_at: Optional[datetime] = None
    discovered_at: datetime
    min_requirements: Optional[List[str]] = None
    preferred_requirements: Optional[List[str]] = None

    class Config:
        from_attributes = True

class ResetResponse(BaseModel):
    jobs_deleted: int
    matches_deleted: int
    companies_deleted: int
    message: str
