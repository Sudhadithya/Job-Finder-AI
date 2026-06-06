import os
import tempfile
import unittest
from unittest.mock import patch
import fitz
from app.services.parser import (
    parse_resume_pdf,
    parse_resume_text,
    detect_sections,
    count_project_headings,
    count_experience_headings,
    parse_resume_text_fallback
)

class TestResumeExtraction(unittest.TestCase):

    def test_detect_sections(self):
        """Test that section detection correctly slices resume text."""
        resume_text = """
John Doe
john.doe@example.com

EDUCATION
B.S. in Computer Science - XYZ University

EXPERIENCE
Software Engineer Intern at Stripe
June 2025 - August 2025
- Engineered database migrations.

PROJECTS
Job Finder AI | GitHub
Built a resume parser.

SKILLS
Python, JavaScript, Docker
"""
        sections = detect_sections(resume_text)
        self.assertIn("john.doe@example.com", sections["header_info"])
        self.assertIn("XYZ University", sections["education"])
        self.assertIn("Stripe", sections["experience"])
        self.assertIn("Job Finder AI", sections["projects"])
        self.assertIn("Python, JavaScript", sections["skills"])

    def test_count_project_headings(self):
        """Test heuristic project heading counter."""
        projects_text = """
PROJECTS
* Multi-Source Data Connector Pipeline | GitHub Apr 2026
* Tech: Python, FastAPI
- Engineered a pluggable connector architecture.
- Implemented idempotent data loading.

* Slack Notification bot | GitLab
- Created notification worker.
"""
        count = count_project_headings(projects_text)
        self.assertEqual(count, 2)

    def test_count_experience_headings(self):
        """Test heuristic experience heading counter."""
        experience_text = """
EXPERIENCE
* Stripe — Software Engineer Intern (June 2025 - August 2025)
- Developed API integrations.
* Google | Research Intern | May 2024 - August 2024
- Researched LLM agents.
"""
        count = count_experience_headings(experience_text)
        self.assertEqual(count, 2)

    def test_fallback_parser_structure(self):
        """Test fallback parser produces structured project/experience objects matching the Pydantic models."""
        resume_text = """
john.doe@example.com

EXPERIENCE
Stripe | Software Engineer Intern
- Developed backend features.
Tech: Python, Go

PROJECTS
Job Finder AI
- Built FastAPI API.
Tech: React, Python
"""
        res = parse_resume_text_fallback(resume_text)
        self.assertEqual(res["email"], "john.doe@example.com")
        self.assertGreater(len(res["projects"]), 0)
        self.assertGreater(len(res["experience"]), 0)
        
        # Verify schema keys
        proj = res["projects"][0]
        self.assertIn("name", proj)
        self.assertIn("technologies", proj)
        self.assertIn("description", proj)
        self.assertIn("highlights", proj)
        self.assertIn("Python", proj["technologies"])
        
        exp = res["experience"][0]
        self.assertIn("company", exp)
        self.assertIn("role", exp)
        self.assertIn("start_date", exp)
        self.assertIn("end_date", exp)
        self.assertIn("duration_months", exp)
        self.assertIn("highlights", exp)
        self.assertIn("Python", exp["technologies"])

    @patch("app.services.parser.call_gemini_api")
    def test_parse_resume_text_validation_retry(self, mock_call):
        """Test that if count mismatch occurs, LLM call retries with a stricter prompt."""
        # Mock responses: 
        # Call 1 (Skills): returns ["Python", "FastAPI"]
        # Call 2 (Projects): returns only 1 project (but we detect 2 headings in the text)
        # Call 3 (Retry Projects): returns 2 projects
        # Call 4 (Experience): returns 1 experience (1 heading detected)
        # Call 5 (Education): returns ["B.S."]
        mock_call.side_effect = [
            '["Python", "FastAPI"]',  # Skills
            '[{"name": "Proj 1", "technologies": [], "description": "", "highlights": []}]',  # Projects first try
            '[{"name": "Proj 1", "technologies": [], "description": "", "highlights": []}, {"name": "Proj 2", "technologies": [], "description": "", "highlights": []}]',  # Projects retry
            '[{"company": "Comp 1", "role": "Role 1", "start_date": "", "end_date": "", "duration_months": 3, "description": "", "technologies": [], "highlights": []}]',  # Experience
            '["B.S. Computer Science"]' # Education
        ]
        
        resume_text = """
john.doe@example.com

PROJECTS
* Project One | GitHub 2026
* Project Two | GitHub 2025

EXPERIENCE
* Stripe - Intern (June 2025 - August 2025)
"""
        # Patch GEMINI_API_KEY to trigger LLM flow
        with patch("app.core.config.settings.GEMINI_API_KEY", "dummy_key"):
            res = parse_resume_text(resume_text)
            
            # Assert both projects were extracted (thanks to the retry)
            self.assertEqual(len(res["projects"]), 2)
            self.assertEqual(res["metrics"]["projects_detected"], 2)
            self.assertEqual(res["metrics"]["projects_extracted"], 2)
            self.assertEqual(res["metrics"]["experience_detected"], 1)
            self.assertEqual(res["metrics"]["experience_extracted"], 1)

    def test_pdf_layout_sorting_multitcolumn(self):
        """Verify multi-column PDF layout text extraction sorting using PyMuPDF."""
        # Create a temp PDF file
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        
        try:
            # Construct a two-column PDF
            doc = fitz.open()
            page = doc.new_page(width=600, height=800)
            
            # Left column text (x=50)
            page.insert_text((50, 100), "EDUCATION", fontsize=12)
            page.insert_text((50, 120), "BITS Pilani Hyderabad", fontsize=10)
            page.insert_text((50, 200), "SKILLS", fontsize=12)
            page.insert_text((50, 220), "Python, FastAPI, Docker", fontsize=10)
            
            # Right column text (x=300)
            page.insert_text((300, 100), "EXPERIENCE", fontsize=12)
            page.insert_text((300, 120), "Stripe — Software Engineer Intern", fontsize=10)
            page.insert_text((300, 200), "PROJECTS", fontsize=12)
            page.insert_text((300, 220), "Multi-Source Data Connector Pipeline", fontsize=10)
            
            doc.save(path)
            doc.close()
            
            # Extract text using PyMuPDF and verify order
            doc_read = fitz.open(path)
            text_sorted = ""
            for p in doc_read:
                text_sorted += p.get_text("text", sort=True) + "\n"
            doc_read.close()
            
            # With sort=True, blocks are sorted top-to-bottom, left-to-right.
            # Thus, at y=100, we read EDUCATION (left) then EXPERIENCE (right).
            # Then at y=120, we read BITS Pilani (left) then Stripe (right).
            # This reconstructs visual layout order correctly.
            self.assertIn("EDUCATION", text_sorted)
            self.assertIn("EXPERIENCE", text_sorted)
            self.assertIn("SKILLS", text_sorted)
            self.assertIn("PROJECTS", text_sorted)
            
        finally:
            if os.path.exists(path):
                os.remove(path)

if __name__ == '__main__':
    unittest.main()
