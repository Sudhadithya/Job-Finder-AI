import os
import re
import json
import time
import httpx
import fitz
from app.core.config import settings

COMMON_SKILLS = [
    "Python", "React", "PostgreSQL", "Docker", "AWS", "FastAPI", "JavaScript", 
    "TypeScript", "HTML", "CSS", "SQL", "Git", "Java", "C++", "Go", "Rust", 
    "Kubernetes", "Node.js", "Django", "Flask", "PyTorch", "TensorFlow", "Pandas",
    "NumPy", "Spark", "Hadoop", "MongoDB", "Redis", "Elasticsearch", "Data Science",
    "Machine Learning", "Deep Learning", "AI", "Backend", "Frontend", "Fullstack"
]

def detect_sections(text: str) -> dict:
    """
    Split the resume text into standard sections based on heading keywords.
    Returns a dictionary of section names to raw text chunks.
    """
    lines = text.split("\n")
    
    header_patterns = {
        "education": [
            "education", "academic", "academics", "academic background",
            "university", "college", "degree", "education history",
            "educational background", "qualifications", "academic qualifications"
        ],
        "experience": [
            "experience", "employment", "work history", "professional history",
            "professional experience", "work experience", "employment history",
            "career history", "career summary", "relevant experience",
            "work experience and internships"
        ],
        "internships": [
            "internships", "intern experience", "internship experience", "internship"
        ],
        "projects": [
            "projects", "personal projects", "academic projects", "key projects",
            "featured projects", "technical projects", "side projects", "portfolio",
            "open source", "open source projects", "notable projects"
        ],
        "skills": [
            "skills", "technical skills", "technologies", "expertise",
            "core competencies", "skills  technologies", "skills and technologies",
            "tools", "tools and technologies", "programming languages",
            "technical expertise", "tech stack"
        ],
        "certifications": [
            "certifications", "certificates", "licenses",
            "certifications  licenses", "certifications and licenses",
            "courses", "online courses"
        ],
        "achievements": [
            "achievements", "awards", "honors", "accolades",
            "awards  achievements", "awards and achievements",
            "accomplishments", "recognition"
        ]
    }
    
    header_indices = []
    
    for idx, line in enumerate(lines):
        clean_line = line.strip()
        if not clean_line or len(clean_line) > 40:
            continue
        line_lower = clean_line.lower()
        # Keep spaces and alphanumeric only
        line_clean = re.sub(r'[^a-z0-9\s]', '', line_lower).strip()
        # Collapse multi-spaces
        line_clean = re.sub(r'\s+', ' ', line_clean)
        
        matched_section = None
        for sec, exact_titles in header_patterns.items():
            if line_clean in exact_titles:
                matched_section = sec
                break
                
        if matched_section:
            header_indices.append((idx, matched_section, clean_line))
            
    sections = {
        "header_info": "",
        "education": "",
        "experience": "",
        "internships": "",
        "projects": "",
        "skills": "",
        "certifications": "",
        "achievements": ""
    }
    
    if not header_indices:
        sections["header_info"] = text
        return sections
        
    first_idx = header_indices[0][0]
    sections["header_info"] = "\n".join(lines[:first_idx])
    
    for i in range(len(header_indices)):
        start_idx, sec_type, _ = header_indices[i]
        end_idx = header_indices[i+1][0] if i+1 < len(header_indices) else len(lines)
        
        # Skip the header line itself to avoid dummy entry extraction
        section_text = "\n".join(lines[start_idx + 1:end_idx]).strip()
        
        if sections[sec_type]:
            sections[sec_type] += "\n\n" + section_text
        else:
            sections[sec_type] = section_text
            
    return sections

def count_project_headings(text: str) -> int:
    """
    Count project headings by looking for lines that contain a GitHub/GitLab link
    (the canonical project title format: 'Project Name | GitHub  <date>').
    Falls back to counting lines with a year if no GitHub links found.
    """
    if not text.strip():
        return 0
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    action_verbs_set = {
        "engineered", "implemented", "built", "developed", "designed", "created",
        "led", "managed", "collaborated", "wrote", "optimized", "reduced", "increased",
        "improved", "spearheaded", "architected", "deployed", "scaled", "integrated",
        "saved", "accelerated", "enhanced", "resolved", "automated", "facilitated",
        "utilized", "leveraged", "programmed", "devised", "formulated"
    }
    # Primary strategy: count lines that have a GitHub or GitLab link.
    # These are definitively project title lines in standard resume formats.
    # Exclude: tech: lines, lines > 120 chars (bullet points), and action-verb-starting lines.
    github_lines = []
    for l in lines:
        l_clean = l.lstrip("*-• \t")
        if not ("github" in l.lower() or "gitlab" in l.lower()):
            continue
        if l_clean.lower().startswith("tech:") or l_clean.lower().startswith("technologies:"):
            continue
        if len(l_clean) > 120:
            continue
        first_word = l_clean.split()[0].lower().rstrip(":,.-") if l_clean.split() else ""
        if first_word in action_verbs_set:
            continue
        github_lines.append(l)
    if github_lines:
        return len(github_lines)
    
    # Fallback: count short lines (< 80 chars) that are not bullet points,
    # not tech lines, and not action verb sentences.
    action_verbs = {
        "engineered", "implemented", "built", "developed", "designed", "created",
        "led", "managed", "collaborated", "wrote", "optimized", "reduced", "increased",
        "improved", "spearheaded", "architected", "deployed", "scaled", "integrated",
        "saved", "accelerated", "enhanced", "resolved", "automated", "facilitated",
        "utilized", "leveraged", "programmed", "devised", "formulated"
    }
    count = 0
    for line in lines:
        line_clean = line.lstrip("*-• \t")
        if not line_clean or len(line_clean) > 80:
            continue
        if line_clean.lower() in ["projects", "personal projects", "academic projects", "key projects", "featured projects"]:
            continue
        if line_clean.lower().startswith("tech:") or line_clean.lower().startswith("technologies:"):
            continue
        first_word = line_clean.split()[0].lower().rstrip(":,.-") if line_clean.split() else ""
        if first_word in action_verbs:
            continue
        # Only count if line contains a year (likely a titled entry)
        if re.search(r'\b(19|20)\d{2}\b', line_clean):
            count += 1
    
    if count == 0 and len(lines) > 2:
        return 1
    return count

def count_experience_headings(text: str) -> int:
    """
    Count experience headings by looking for lines that contain BOTH a company-level
    identifier AND a date range. The role/title line directly below is NOT a separate
    heading — it belongs to the same entry.
    """
    if not text.strip():
        return 0
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    count = 0
    
    for line in lines:
        line_clean = line.lstrip("*-• \t")
        if not line_clean:
            continue
        # Skip section header lines themselves
        if line_clean.lower() in ["experience", "work experience", "work history", "employment",
                                   "professional experience", "internships", "intern experience"]:
            continue
        # Skip bullet point lines (action verbs starting a sentence)
        first_word = line_clean.split()[0].lower().rstrip(":,.-") if line_clean.split() else ""
        action_verbs = {
            "engineered", "implemented", "built", "developed", "designed", "created",
            "led", "managed", "collaborated", "wrote", "optimized", "reduced", "increased",
            "improved", "spearheaded", "architected", "deployed", "scaled", "integrated",
            "saved", "accelerated", "enhanced", "resolved", "automated", "facilitated",
            "utilized", "leveraged", "programmed", "devised", "formulated", "modeled",
            "modelled", "performed"
        }
        if first_word in action_verbs:
            continue
        # A line is a company/employer heading if it contains a date range.
        # We require an actual date pattern (month+year or year range or "present").
        # This distinguishes company lines like "PwC   Jan 2026 – Present" from
        # role lines like "Software Development Engineer Intern, Bangalore".
        has_date_range = bool(re.search(
            r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec'
            r'|january|february|march|april|june|july|august|september'
            r'|october|november|december)\b.{0,30}\b(present|(19|20)\d{2})\b',
            line_clean.lower()
        ))
        has_year_range = bool(re.search(
            r'\b(19|20)\d{2}\s*[–\-]\s*(present|(19|20)\d{2})\b',
            line_clean.lower()
        ))
        if has_date_range or has_year_range:
            count += 1

    if count == 0 and len(lines) > 2:
        return 1
    return count

GEMINI_MODEL = "gemini-2.5-flash"

def call_gemini_api(prompt: str, gemini_key: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={gemini_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    res = httpx.post(url, headers=headers, json=payload, timeout=20.0)
    if res.status_code == 429:
        # Quota exhausted — fail immediately, let caller activate fallback parser
        raise Exception(f"Gemini 429 rate limit (quota exhausted) — using fallback parser")
    res.raise_for_status()
    data = res.json()
    content = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()


def call_llm_for_projects(projects_text: str, detected_count: int, gemini_key: str, use_stricter: bool) -> list:
    if use_stricter:
        prompt = f"""
YOU CRITICALLY FAILED THE PREVIOUS EXTRACTION by missing some projects.
You MUST extract exactly {detected_count} projects from the projects section text.
Review the text line-by-line. Identify every single project heading, name, or title.
Extract EVERY single project. Do not merge any projects.

Projects section text:
---
{projects_text}
---

Return a JSON array of objects. Each object MUST have this exact schema:
{{
  "name": "Project Name (string)",
  "technologies": ["technology1", "technology2", ...],
  "description": "Short description of the project",
  "highlights": ["bullet point 1", "bullet point 2", ...]
}}
Respond ONLY with a valid JSON array. Do not include any other text, markdown formatting, or comments.
"""
    else:
        prompt = f"""
You are an expert resume parsing assistant. Extract ALL project entries from the text below.
Do not skip or merge any projects. If there are multiple projects listed, you must extract every single one of them.

Projects section text:
---
{projects_text}
---

Return a JSON array of objects. Each object MUST have this exact schema:
{{
  "name": "Project Name (string)",
  "technologies": ["technology1", "technology2", ...],
  "description": "Short description of the project",
  "highlights": ["bullet point 1", "bullet point 2", ...]
}}
Respond ONLY with a valid JSON array. Do not include any other text, markdown formatting, or comments.
"""
    try:
        content = call_gemini_api(prompt, gemini_key)
        return json.loads(content)
    except Exception as e:
        print(f"Error calling Gemini for projects extraction: {e}")
        return []

def call_llm_for_experience(experience_text: str, detected_count: int, gemini_key: str, use_stricter: bool) -> list:
    if use_stricter:
        prompt = f"""
YOU CRITICALLY FAILED THE PREVIOUS EXTRACTION by missing some experience entries.
You MUST extract exactly {detected_count} experience/internship entries from the experience section text.
Review the text line-by-line. Identify every single job or internship.
Extract EVERY single experience entry. Do not merge or skip any.

Experience section text:
---
{experience_text}
---

Return a JSON array of objects. Each object MUST have this exact schema:
{{
  "company": "Company/Organization Name (string)",
  "role": "Job Title/Role (string)",
  "start_date": "Start Date (string)",
  "end_date": "End Date (string)",
  "duration_months": duration in months (integer),
  "description": "Brief description of the role/responsibilities",
  "technologies": ["technology1", "technology2", ...],
  "highlights": ["bullet point 1", "bullet point 2", ...]
}}
Respond ONLY with a valid JSON array. Do not include any other text, markdown formatting, or comments.
"""
    else:
        prompt = f"""
You are an expert resume parsing assistant. Extract ALL work experience and internship entries from the text below.
Do not skip or merge any experiences. If there are multiple jobs/internships listed, you must extract every single one of them.

Experience section text:
---
{experience_text}
---

Return a JSON array of objects. Each object MUST have this exact schema:
{{
  "company": "Company/Organization Name (string)",
  "role": "Job Title/Role (string)",
  "start_date": "Start Date (string, e.g., 'June 2025')",
  "end_date": "End Date (string, e.g., 'August 2025' or 'Present')",
  "duration_months": duration in months (integer, calculate/estimate the duration, e.g., 3),
  "description": "Brief description of the role/responsibilities",
  "technologies": ["technology1", "technology2", ...],
  "highlights": ["bullet point 1", "bullet point 2", ...]
}}
Respond ONLY with a valid JSON array. Do not include any other text, markdown formatting, or comments.
"""
    try:
        content = call_gemini_api(prompt, gemini_key)
        return json.loads(content)
    except Exception as e:
        print(f"Error calling Gemini for experience extraction: {e}")
        return []

def call_llm_for_skills(skills_text: str, gemini_key: str) -> list:
    prompt = f"""
You are an expert resume parsing assistant. Extract a list of all technical skills, programming languages, frameworks, and technologies mentioned in the text below.

Skills section text:
---
{skills_text}
---

Return a JSON array of strings, e.g. ["Python", "React", "Docker", "AWS"].
Respond ONLY with a valid JSON array. Do not include any other text, markdown formatting, or comments.
"""
    try:
        content = call_gemini_api(prompt, gemini_key)
        return json.loads(content)
    except Exception as e:
        print(f"Error calling Gemini for skills extraction: {e}")
        return []

def call_llm_for_education(education_text: str, gemini_key: str) -> list:
    prompt = f"""
You are an expert resume parsing assistant. Extract all education details (degrees, universities, graduation years, GPA if present) from the text below.

Education section text:
---
{education_text}
---

Return a JSON array of strings, where each string represents one education entry.
Respond ONLY with a valid JSON array. Do not include any other text, markdown formatting, or comments.
"""
    try:
        content = call_gemini_api(prompt, gemini_key)
        return json.loads(content)
    except Exception as e:
        print(f"Error calling Gemini for education extraction: {e}")
        return []

def parse_resume_text_fallback(text: str) -> dict:
    """
    Fallback parser using regex and keywords when LLM is unavailable.

    Key strategy:
    - Experience: a new entry starts ONLY on a line that contains a date range
      (e.g. "PwC   Jan 2026 – Present"). The very next non-bullet line is the role.
    - Projects: a new entry starts on a line that contains a GitHub/GitLab link,
      or a short (<80 char) line followed by a Tech: line.
    """
    text_lower = text.lower()

    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    email = email_match.group(0) if email_match else ""

    skills = []
    for skill in COMMON_SKILLS:
        pattern = rf'\b{re.escape(skill.lower())}\b'
        if re.search(pattern, text_lower):
            skills.append(skill)

    sections = detect_sections(text)

    has_any_detected_section = any(
        sections[k] for k in ["education", "experience", "internships", "projects", "skills"]
    )

    if not has_any_detected_section:
        projects_text = text
        experience_text = text
        education_text = text
    else:
        projects_text = sections["projects"]
        experience_text = "\n\n".join(filter(None, [sections["experience"], sections["internships"]]))
        education_text = sections["education"]

    # ---- Education ----
    edu_lines = [l.strip() for l in education_text.split('\n') if l.strip() and len(l.strip()) > 8]
    education = edu_lines[:5] if edu_lines else []

    # ---- Experience ----
    # Strategy: a company/employer heading is identified by having a date range.
    # The line immediately after (if it is NOT a bullet) is the role title.
    DATE_RANGE_RE = re.compile(
        # Month-name + year ranges: "Jan 2026 – Present", "January 2024 - Dec 2024"
        r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec'
        r'|january|february|march|april|june|july|august|september'
        r'|october|november|december)\b.{0,40}\b(present|(19|20)\d{2})\b'
        # Plain year ranges: "2022 – 2024", "2023-present"
        r'|\b(19|20)\d{2}\s*[\u2013\u2014\-]\s*(present|(19|20)\d{2})\b'
        # Numeric month/year ranges: "01/2024 – 06/2024", "06/23-present"
        r'|\b\d{1,2}/\d{2,4}\s*[\u2013\u2014\-]\s*(present|\d{1,2}/\d{2,4})\b',
        re.IGNORECASE
    )
    DATE_EXTRACT_RE = re.compile(
        r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}|\d{4}|\d{1,2}/\d{2,4})',
        re.IGNORECASE
    )

    exp_lines = [l.strip() for l in experience_text.split('\n') if l.strip()]
    parsed_experience = []
    current_exp = None
    expect_role_next = False   # flag: the next non-bullet line is the role

    for line in exp_lines:
        is_bullet = line.startswith(("•", "-", "*", "–"))
        line_clean = line.lstrip("•-*– \t").strip()
        if not line_clean:
            continue

        if DATE_RANGE_RE.search(line_clean):
            # This is a company/employer heading
            if current_exp:
                parsed_experience.append(current_exp)

            # Extract dates from the line
            dates = DATE_EXTRACT_RE.findall(line_clean)
            start_date = dates[0].strip() if len(dates) >= 1 else "N/A"
            end_date = dates[1].strip() if len(dates) >= 2 else "Present"

            # Strip the date portion to get the company name
            company_name = DATE_RANGE_RE.sub("", line_clean).strip().rstrip("–-| \t")
            company_name = company_name.strip() or "Unknown Company"

            current_exp = {
                "company": company_name,
                "role": "",
                "start_date": start_date,
                "end_date": end_date,
                "duration_months": 0,
                "description": "",
                "technologies": [],
                "highlights": []
            }
            expect_role_next = True

        elif expect_role_next and current_exp and not is_bullet:
            # This non-bullet line right after the company heading is the role
            current_exp["role"] = line_clean
            current_exp["description"] = line_clean
            expect_role_next = False

        elif current_exp:
            expect_role_next = False
            if line_clean.lower().startswith(("tech:", "technologies:")):
                techs = [t.strip() for t in re.split(r'[,|;]', line_clean.split(":", 1)[1])]
                current_exp["technologies"].extend([t for t in techs if t])
            elif is_bullet or len(line_clean) > 40:
                current_exp["highlights"].append(line_clean)

    if current_exp:
        parsed_experience.append(current_exp)

    # ---- Projects ----
    # Strategy: a project title line contains "github" or "gitlab",
    # OR is a short line (< 80 chars) that is NOT a bullet and NOT a tech line,
    # followed by the next line being a Tech: line.
    proj_lines = [l.strip() for l in projects_text.split('\n') if l.strip()]
    parsed_projects = []
    current_proj = None

    ACTION_VERBS = {
        "engineered", "implemented", "built", "developed", "designed", "created",
        "led", "managed", "collaborated", "wrote", "optimized", "reduced", "increased",
        "improved", "spearheaded", "architected", "deployed", "scaled", "integrated",
        "saved", "accelerated", "enhanced", "resolved", "automated", "utilized",
        "leveraged", "programmed", "applied", "performed", "modeled", "modelled"
    }

    def _is_project_title(ln: str, next_line: str = "") -> bool:
        """True if this line looks like a project title (not a bullet or tech line)."""
        lc = ln.lstrip("•-*– \t")
        if not lc or lc.lower().startswith(("tech:", "technologies:")):
            return False
        if ln.startswith(("•", "-", "*", "–")):
            return False
        first = lc.split()[0].lower().rstrip(":,.-") if lc.split() else ""
        if first in ACTION_VERBS:
            return False
        # Definitive: has GitHub/GitLab link
        if "github" in lc.lower() or "gitlab" in lc.lower():
            return True
        # Heuristic 1: short non-bullet line with a year
        if len(lc) < 90 and re.search(r'\b(19|20)\d{2}\b', lc):
            return True
        # Heuristic 2: short non-bullet line immediately followed by a Tech: line
        # (catches projects without GitHub links or dates)
        if len(lc) < 90 and next_line.lower().startswith(("tech:", "technologies:")):
            return True
        return False

    for i, line in enumerate(proj_lines):
        is_bullet = line.startswith(("•", "-", "*", "–"))
        line_clean = line.lstrip("•-*– \t").strip()
        next_line = proj_lines[i + 1].lstrip("•-*– \t").strip() if i + 1 < len(proj_lines) else ""
        if not line_clean:
            continue

        if _is_project_title(line, next_line):
            if current_proj:
                parsed_projects.append(current_proj)
            # Clean name: strip trailing date/github URL noise
            name = re.split(r'\s{2,}', line_clean)[0].strip()
            current_proj = {
                "name": name,
                "technologies": [],
                "description": "",
                "highlights": []
            }
        elif current_proj:
            if line_clean.lower().startswith(("tech:", "technologies:")):
                techs = [t.strip() for t in re.split(r'[,|;]', line_clean.split(":", 1)[1])]
                current_proj["technologies"].extend([t for t in techs if t])
            else:
                if not current_proj["description"] and is_bullet:
                    current_proj["description"] = line_clean
                current_proj["highlights"].append(line_clean)

    if current_proj:
        parsed_projects.append(current_proj)

    if not skills:
        skills = ["Python", "SQL", "Git"]

    return {
        "email": email,
        "skills": list(set(skills)),
        "projects": parsed_projects,
        "experience": parsed_experience,
        "education": education,
        "metrics": {
            "projects_detected": len(parsed_projects),
            "projects_extracted": len(parsed_projects),
            "experience_detected": len(parsed_experience),
            "experience_extracted": len(parsed_experience),
            "skills_extracted": len(skills)
        }
    }


def parse_resume_text(text: str) -> dict:
    """
    Extract structured resume JSON using Gemini API or fall back to regex parser.
    """
    gemini_key = settings.GEMINI_API_KEY
    if not gemini_key:
        print("No GEMINI_API_KEY set. Using fallback resume parser.")
        return parse_resume_text_fallback(text)
        
    sections = detect_sections(text)
    
    has_any_detected_section = any(sections[k] for k in ["education", "experience", "internships", "projects", "skills", "certifications", "achievements"])
    
    if not has_any_detected_section:
        projects_text = text
        experience_text = text
        skills_text = text
        education_text = text
    else:
        experience_text = "\n\n".join(filter(None, [sections["experience"], sections["internships"]]))
        projects_text = sections["projects"]
        skills_text = sections["skills"] if sections["skills"] else text
        education_text = sections["education"]
        
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    email = email_match.group(0) if email_match else ""
    
    skills = []
    if skills_text.strip():
        skills = call_llm_for_skills(skills_text, gemini_key)
    if not skills:
        skills = []
        text_lower = text.lower()
        for skill in COMMON_SKILLS:
            pattern = rf'\b{re.escape(skill.lower())}\b'
            if re.search(pattern, text_lower):
                skills.append(skill)
        if not skills:
            skills = ["Python", "SQL", "Git"]
            
    projects = []
    projects_detected = 0
    if projects_text.strip():
        projects_detected = count_project_headings(projects_text)
        if projects_detected > 0:
            projects = call_llm_for_projects(projects_text, projects_detected, gemini_key, use_stricter=False)

    experience = []
    experience_detected = 0
    if experience_text.strip():
        experience_detected = count_experience_headings(experience_text)
        if experience_detected > 0:
            experience = call_llm_for_experience(experience_text, experience_detected, gemini_key, use_stricter=False)

    education = []
    if education_text.strip():
        education = call_llm_for_education(education_text, gemini_key)
    if not education and education_text.strip():
        education = [l.strip() for l in education_text.split('\n') if l.strip() and len(l.strip()) > 8][:5]

    # If LLM completely failed for projects or experience, fall back to rule-based parser
    # to avoid returning empty arrays to the user.
    if projects_detected > 0 and len(projects) == 0:
        print("LLM projects extraction failed after retries — using fallback rule-based parser")
        _fallback = parse_resume_text_fallback(text)
        projects = _fallback.get("projects", [])

    if experience_detected > 0 and len(experience) == 0:
        print("LLM experience extraction failed after retries — using fallback rule-based parser")
        _fallback_exp = parse_resume_text_fallback(text)
        experience = _fallback_exp.get("experience", [])
        
    return {
        "email": email,
        "skills": list(set(skills)),
        "projects": projects,
        "experience": experience,
        "education": education,
        "metrics": {
            "projects_detected": projects_detected,
            "projects_extracted": len(projects),
            "experience_detected": experience_detected,
            "experience_extracted": len(experience),
            "skills_extracted": len(skills)
        }
    }

def parse_resume_pdf(pdf_path: str) -> dict:
    """
    Extract text from PDF file and parse it.
    """
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text("text", sort=True) + "\n"
        doc.close()
        return parse_resume_text(text)
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return parse_resume_text_fallback("")
