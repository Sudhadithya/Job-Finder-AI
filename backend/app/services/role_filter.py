"""
role_filter.py — Role classification engine for SDE-1 and Data Scientist tracks.

Produces one of four verdicts for a given job title + user category:
  PRIORITY   — title matches the user's target level well
  NEUTRAL    — title is tech-relevant but not specifically targeted
  PENALIZED  — title is tech but a poor match (score penalty applied)
  EXCLUDED   — title should never enter the pipeline for this user
"""
import re
from typing import Literal

RoleVerdict = Literal["PRIORITY", "NEUTRAL", "PENALIZED", "EXCLUDED"]

# ---------------------------------------------------------------------------
# Hard-exclude words (apply to ALL categories)
# Uses whole-word matching to avoid false positives (e.g. "sr" in "senior")
# ---------------------------------------------------------------------------
GLOBAL_EXCLUDE_WORDS = [
    "senior", "sr", "staff", "principal", "lead", "architect",
    "manager", "director", "vp", "vice president", "head of",
    "cto", "cpo", "ceo",
]

# ---------------------------------------------------------------------------
# SDE-1 track
# ---------------------------------------------------------------------------
SDE1_PRIORITY_PHRASES = [
    "software engineer", "software development engineer",
    "sde-1", "sde i", "sde1",
    "associate software engineer", "associate engineer",
    "backend engineer", "back-end engineer",
    "frontend engineer", "front-end engineer",
    "full stack engineer", "fullstack engineer",
    "software developer", "application engineer",
    "graduate engineer", "new grad", "new graduate",
    "entry level software", "entry-level software",
    "junior software", "junior engineer",
    "member of technical staff",  # common in Databricks, Salesforce etc.
]

SDE1_PENALIZE_PHRASES = [
    "devops", "site reliability", "sre", "platform engineer",
    "infrastructure engineer", "cloud engineer",
    "qa engineer", "test engineer", "quality engineer",
    "support engineer", "technical support",
    "data engineer",  # when user wants SDE-1, not Data Engineer
    "security engineer",
    "solutions engineer", "sales engineer",
]

# ---------------------------------------------------------------------------
# Data Scientist track
# ---------------------------------------------------------------------------
DS_PRIORITY_PHRASES = [
    "data scientist", "senior data scientist",  # 'senior' already excluded globally
    "machine learning engineer", "ml engineer",
    "ai engineer", "artificial intelligence engineer",
    "applied scientist", "research scientist",
    "research engineer",
    "data science",
]

DS_PENALIZE_PHRASES = [
    "data analyst", "business analyst", "bi analyst",
    "data engineer",   # closer to SDE than DS
    "analytics engineer",
    "database administrator", "dba",
]


def _normalize(text: str) -> str:
    return text.lower().strip()


def _contains_exclude_word(title_lower: str) -> bool:
    """Check for global seniority/management exclusions using word-boundary matching."""
    # Use word boundaries for single-word terms
    for word in GLOBAL_EXCLUDE_WORDS:
        if " " in word:
            # Phrase check (e.g. "head of", "vice president")
            if word in title_lower:
                return True
        else:
            # Whole-word check
            if re.search(rf'\b{re.escape(word)}\b', title_lower):
                return True
    return False


def _phrase_match(title_lower: str, phrases: list[str]) -> bool:
    return any(phrase in title_lower for phrase in phrases)


def classify_role(job_title: str, user_category: str | None) -> RoleVerdict:
    """
    Classify a job title against the user's selected category.

    Args:
        job_title:      The raw job title from the ATS posting.
        user_category:  User's desired category ("SDE-1", "Data Scientist", etc.)

    Returns:
        RoleVerdict ("PRIORITY" | "NEUTRAL" | "PENALIZED" | "EXCLUDED")
    """
    title_lower = _normalize(job_title)
    cat_lower = _normalize(user_category or "")

    # 1. Global hard-exclude (seniority/management)
    if _contains_exclude_word(title_lower):
        return "EXCLUDED"

    # 2. Category-specific logic
    if "sde" in cat_lower or "software" in cat_lower or "developer" in cat_lower or "engineer" in cat_lower:
        # SDE-1 track
        if _phrase_match(title_lower, SDE1_PENALIZE_PHRASES):
            return "PENALIZED"
        if _phrase_match(title_lower, SDE1_PRIORITY_PHRASES):
            return "PRIORITY"
        # Generic tech role — neutral
        generic_tech = ["engineer", "developer", "programmer", "scientist", "analyst", "researcher"]
        if any(w in title_lower for w in generic_tech):
            return "NEUTRAL"
        return "EXCLUDED"

    elif "data scientist" in cat_lower or "data science" in cat_lower or "ml" in cat_lower or "machine learning" in cat_lower:
        # Data Scientist track
        if _phrase_match(title_lower, DS_PENALIZE_PHRASES):
            return "PENALIZED"
        if _phrase_match(title_lower, DS_PRIORITY_PHRASES):
            return "PRIORITY"
        # Generic data/ML role — neutral
        generic_data = ["data", "machine learning", "ml", "ai", "research", "analytics"]
        if any(w in title_lower for w in generic_data):
            return "NEUTRAL"
        return "EXCLUDED"

    else:
        # Unknown/no category — fall back to minimal filtering only
        # Exclude only clearly non-tech roles
        non_tech = ["support", "sales", "marketing", "recruiter", "finance", "hr ", "legal"]
        if any(w in title_lower for w in non_tech):
            return "EXCLUDED"
        return "NEUTRAL"


def verdict_to_score_adjustment(verdict: RoleVerdict) -> int:
    """
    Return a score adjustment (additive to base alignment score) for a verdict.
    Used in ranking.py to refine the role_alignment component.
    """
    return {
        "PRIORITY":  +20,
        "NEUTRAL":     0,
        "PENALIZED": -30,
        "EXCLUDED":  -100,  # Should never be stored, but safety net
    }[verdict]
