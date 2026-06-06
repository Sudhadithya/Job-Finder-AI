from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.models import Job, Match, Resume, DiscoveredCompany
from app.api.profile import get_default_user
from app.services.discovery import run_job_discovery
from app.services.matcher import match_resume_to_job
from app.services.ranking import calculate_role_alignment, calculate_final_score
from app.schemas.schemas import (
    DiscoverJobsResponse, MatchRecommendationResponse, JobResponse, ResetResponse, BoardFailure
)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


# ---------------------------------------------------------------------------
# Phase 1: Reset endpoint
# ---------------------------------------------------------------------------
@router.post("/reset", response_model=ResetResponse)
def reset_job_data(db: Session = Depends(get_db)):
    """
    Clear all discovered jobs, matches, and company boards.
    Keeps users and resumes (including parsed JSON and deduplication IDs).
    """
    try:
        matches_deleted = db.query(Match).delete()
        jobs_deleted = db.query(Job).delete()
        companies_deleted = db.query(DiscoveredCompany).delete()
        db.commit()
        return ResetResponse(
            jobs_deleted=jobs_deleted,
            matches_deleted=matches_deleted,
            companies_deleted=companies_deleted,
            message=(
                f"Reset complete. Deleted {jobs_deleted} jobs, "
                f"{matches_deleted} matches, {companies_deleted} company boards. "
                "User profiles and resumes preserved."
            )
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Reset failed: {e}")


# ---------------------------------------------------------------------------
# List jobs
# ---------------------------------------------------------------------------
@router.get("", response_model=List[JobResponse])
def get_jobs(db: Session = Depends(get_db)):
    """Retrieve all stored jobs, newest first."""
    jobs = db.query(Job).order_by(Job.discovered_at.desc()).all()
    return jobs


# ---------------------------------------------------------------------------
# Discover jobs
# ---------------------------------------------------------------------------
@router.post("/discover", response_model=DiscoverJobsResponse)
async def discover_jobs(db: Session = Depends(get_db)):
    """
    Run the full job discovery pipeline.
    The user's desired_category is used for role filtering.
    """
    try:
        user = get_default_user(db)
        user_category = user.desired_category if user else None

        metrics = await run_job_discovery(db, user_category=user_category)

        board_failures = [
            BoardFailure(**f) for f in metrics.get("_board_failures", [])
        ]

        return DiscoverJobsResponse(
            companies_checked=metrics["companies_checked"],
            active_boards_found=metrics["active_boards_found"],
            jobs_discovered=metrics["jobs_discovered"],
            jobs_after_role_filter=metrics["jobs_after_role_filter"],
            jobs_after_location_filter=metrics["jobs_after_location_filter"],
            jobs_recommended=metrics["jobs_recommended"],
            # Backwards-compat fields
            new_jobs_found=metrics["jobs_recommended"],
            boards_attempted=metrics.get("_boards_attempted", 0),
            boards_successful=metrics.get("_boards_successful", 0),
            boards_failed=metrics.get("_boards_failed", 0),
            board_failures=board_failures,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Discovery failed: {e}")


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------
@router.get("/recommendations", response_model=List[MatchRecommendationResponse])
def get_recommendations(db: Session = Depends(get_db)):
    user = get_default_user(db)

    # Check if user has uploaded a resume
    resume = db.query(Resume).filter_by(user_id=user.id).first()
    if not resume:
        raise HTTPException(status_code=400, detail="No resume found. Please upload a resume first.")

    # Get all jobs
    jobs = db.query(Job).all()

    # Re-evaluate or add matches for all jobs
    for job in jobs:
        existing_match = db.query(Match).filter_by(user_id=user.id, job_id=job.job_id).first()
        if not existing_match:
            try:
                match_res = match_resume_to_job(
                    resume_json=resume.parsed_json,
                    job_role=job.role,
                    job_description=job.description
                )

                alignment_score = calculate_role_alignment(
                    job_title=job.role,
                    user_category=user.desired_category
                )

                final_score = calculate_final_score(
                    skill_match=match_res.get("skill_match_score", 0),
                    project_match=match_res.get("project_match_score", 0),
                    experience_match=match_res.get("experience_match_score", 0),
                    education_match=match_res.get("education_match_score", 0),
                    role_alignment=alignment_score
                )

                if final_score >= 60:
                    new_match = Match(
                        user_id=user.id,
                        job_id=job.job_id,
                        score=final_score,
                        matching_skills=match_res.get("matching_skills", []),
                        missing_skills=match_res.get("missing_skills", []),
                        reasoning=match_res.get("reasoning", "")
                    )
                    db.add(new_match)
            except Exception as e:
                print(f"Failed to match job {job.job_id}: {e}")
                continue

    db.commit()

    # Query all matches for user
    db_matches = db.query(Match).filter_by(user_id=user.id).all()

    recommendations = []
    for m in db_matches:
        job_item = db.query(Job).filter_by(job_id=m.job_id).first()
        if job_item:
            recommendations.append(MatchRecommendationResponse(
                id=m.id,
                user_id=m.user_id,
                job_id=m.job_id,
                score=m.score,
                matching_skills=m.matching_skills,
                missing_skills=m.missing_skills,
                reasoning=m.reasoning,
                created_at=m.created_at,
                company=job_item.company,
                role=job_item.role,
                job_url=job_item.job_url
            ))

    recommendations.sort(key=lambda x: x.score, reverse=True)
    return recommendations
