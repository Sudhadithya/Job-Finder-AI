import unittest
from app.services.parser import parse_resume_text_fallback

class TestParser(unittest.TestCase):
    def test_parse_resume_text_fallback_empty(self):
        """Test fallback parser handles empty input gracefully by providing realistic defaults."""
        res = parse_resume_text_fallback("")
        self.assertIsInstance(res, dict)
        self.assertIn("skills", res)
        self.assertIn("projects", res)
        self.assertIn("experience", res)
        self.assertIn("education", res)
        self.assertGreater(len(res["skills"]), 0)

    def test_parse_resume_text_fallback_with_keywords(self):
        """Test fallback parser detects specific skills mentioned in resume."""
        resume_text = """
        John Doe
        Resume
        Experience: Software Engineer at Stripe
        Skills: Python, React, PostgreSQL, Docker, AWS
        Projects: Build an API using FastAPI
        Education: BS in Computer Science
        """
        res = parse_resume_text_fallback(resume_text)
        
        # Assert skills are extracted
        self.assertIn("Python", res["skills"])
        self.assertIn("React", res["skills"])
        self.assertTrue(
            "Postgresql" in res["skills"] or 
            "PostgreSQL" in res["skills"] or 
            "POSTGRESQL" in res["skills"]
        )
        self.assertIn("Docker", res["skills"])
        self.assertTrue(
            "Aws" in res["skills"] or 
            "AWS" in res["skills"]
        )
        
        # Assert experience / education contain the lines
        self.assertTrue(any("Stripe" in str(exp) for exp in res["experience"]))
        self.assertTrue(any("FastAPI" in str(proj) for proj in res["projects"]))
        self.assertTrue(any("BS in Computer Science" in edu for edu in res["education"]))

if __name__ == '__main__':
    unittest.main()
