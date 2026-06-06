from app.services.role_filter import classify_role, verdict_to_score_adjustment

def calculate_role_alignment(job_title: str, user_category: str | None) -> int:
    """
    Calculate the role alignment score (0-100) based on the user's target category.

    Uses the RoleFilter verdict:
      PRIORITY   -> base 90 + 20 adjustment (capped at 100)
      NEUTRAL    -> base 70
      PENALIZED  -> base 70 - 30 = 40
      EXCLUDED   -> 0  (should never reach recommendations, but safety net)
    """
    if not job_title:
        return 50

    verdict = classify_role(job_title, user_category)

    base_scores = {
        "PRIORITY":  90,
        "NEUTRAL":   70,
        "PENALIZED": 70,
        "EXCLUDED":   0,
    }

    base = base_scores[verdict]
    adjustment = verdict_to_score_adjustment(verdict)
    role_alignment = base + adjustment
    return max(0, min(100, role_alignment))


def calculate_final_score(
    skill_match: int,
    project_match: int,
    experience_match: int,
    education_match: int,
    role_alignment: int
) -> int:
    """
    Apply the ranking formula:
    final_score = skill_match * 0.45 + project_match * 0.25
                + experience_match * 0.15 + education_match * 0.05
                + role_alignment * 0.10
    """
    score = (
        skill_match * 0.45 +
        project_match * 0.25 +
        experience_match * 0.15 +
        education_match * 0.05 +
        role_alignment * 0.10
    )
    return max(0, min(100, round(score)))
