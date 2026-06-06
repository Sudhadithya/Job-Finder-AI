import unittest
from app.services.matcher import match_resume_to_job_fallback

class TestMatcher(unittest.TestCase):
    def test_match_resume_to_job_fallback(self):
        """Verify that matching and missing skills are identified from descriptions."""
        resume = {
            "skills": ["Python", "FastAPI", "React", "SQL"],
            "projects": [],
            "experience": ["Intern SDE"],
            "education": []
        }
        
        job_desc = "We need a Python developer who is familiar with Docker and PostgreSQL."
        
        res = match_resume_to_job_fallback(
            resume_json=resume,
            job_role="Software Engineer",
            job_description=job_desc
        )
        
        self.assertIsInstance(res, dict)
        self.assertIn("skill_match_score", res)
        self.assertIn("matching_skills", res)
        self.assertIn("missing_skills", res)
        
        # Assert skills are correctly classified
        self.assertIn("Python", res["matching_skills"])
        self.assertIn("Docker", res["missing_skills"])

if __name__ == '__main__':
    unittest.main()
