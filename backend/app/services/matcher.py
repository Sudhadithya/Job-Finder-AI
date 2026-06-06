import os
import re
import json
import httpx
from app.core.config import settings
from app.services.parser import COMMON_SKILLS

GEMINI_MODEL = "gemini-2.5-flash"

def match_resume_to_job_fallback(resume_json: dict, job_role: str, job_description: str) -> dict:
    """
    Fallback matcher using basic keyword matching.
    """
    desc_lower = job_description.lower()
    user_skills = resume_json.get("skills", [])
    user_skills_lower = {s.lower() for s in user_skills}
    
    # Extract matching skills (skills user has that are in description)
    matching_skills = []
    for skill in user_skills:
        # Match using word boundaries or simple substring search
        if skill.lower() in desc_lower:
            matching_skills.append(skill)
            
    # Extract missing skills (skills in description that user doesn't have)
    missing_skills = []
    for skill in COMMON_SKILLS:
        if skill.lower() in desc_lower and skill.lower() not in user_skills_lower:
            missing_skills.append(skill)
            
    # Calculate skill match score
    total_req_skills = len(matching_skills) + len(missing_skills)
    if total_req_skills > 0:
        skill_match_score = int((len(matching_skills) / total_req_skills) * 100)
    else:
        skill_match_score = 70
        
    reasoning = (
        f"Regex Matcher: Found {len(matching_skills)} matching skills ({', '.join(matching_skills)}). "
        f"Identified {len(missing_skills)} missing skills from the job description ({', '.join(missing_skills[:3]) if missing_skills else 'none'})."
    )
    
    return {
        "skill_match_score": skill_match_score,
        "project_match_score": 75,
        "experience_match_score": 70,
        "education_match_score": 80,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "reasoning": reasoning
    }

def match_resume_to_job(resume_json: dict, job_role: str, job_description: str) -> dict:
    """
    Match candidate resume to job details using Gemini API, with a local regex fallback.
    """
    gemini_key = settings.GEMINI_API_KEY
    if not gemini_key:
        return match_resume_to_job_fallback(resume_json, job_role, job_description)
        
    prompt = f"""
You are a job matching assistant. Compare the candidate's resume and the job details below:
Candidate Resume details (JSON):
{json.dumps(resume_json, indent=2)}

Job Title/Role: {job_role}
Job Description:
{job_description}

Evaluate the candidate and return a JSON object with:
{{
  "skill_match_score": integer (0 to 100 representing how well resume skills match job requirements),
  "project_match_score": integer (0 to 100 representing how well projects align with the role),
  "experience_match_score": integer (0 to 100 representing how well experience aligns),
  "education_match_score": integer (0 to 100 representing how well education aligns),
  "matching_skills": list of strings (skills found in both resume and job description),
  "missing_skills": list of strings (skills in job description but missing from resume),
  "reasoning": string (concise explanation of match)
}}
Respond ONLY with a valid JSON object. Do not include any other text, markdown formatting (do NOT wrap it in ```json), or comments.
"""

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={gemini_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }
        res = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        res.raise_for_status()
        data = res.json()
        content = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        # Clean markdown code blocks if any
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        return json.loads(content)
    except Exception as e:
        print(f"Error calling Gemini for job matching: {e}. Falling back to keyword matcher.")
        return match_resume_to_job_fallback(resume_json, job_role, job_description)
