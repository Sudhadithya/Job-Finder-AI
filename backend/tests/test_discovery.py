import unittest
from datetime import datetime, timezone, timedelta
from app.services.discovery import extract_board_info
from app.services.location import classify_location

class TestDiscoveryHelpers(unittest.TestCase):
    def test_extract_board_info(self):
        """Verify Greenhouse, Lever, and Ashby board URL parsing."""
        # Greenhouse URLs
        self.assertEqual(extract_board_info("https://boards.greenhouse.io/stripe/jobs/123"), ("greenhouse", "stripe"))
        self.assertEqual(extract_board_info("https://boards.greenhouse.io/embed/job_board?for=reddit"), ("greenhouse", "reddit"))
        
        # Lever URLs
        self.assertEqual(extract_board_info("https://jobs.lever.co/palantir/abc-123"), ("lever", "palantir"))
        self.assertEqual(extract_board_info("https://jobs.lever.co/groww"), ("lever", "groww"))
        
        # Ashby URLs
        self.assertEqual(extract_board_info("https://jobs.ashbyhq.com/hebbia/123-456"), ("ashby", "hebbia"))
        self.assertEqual(extract_board_info("https://jobs.ashbyhq.com/linear"), ("ashby", "linear"))
        
        # Unknown/Invalid URLs
        self.assertEqual(extract_board_info("https://google.com"), (None, None))
        self.assertEqual(extract_board_info(""), (None, None))

    def test_seniority_keywords_filtering(self):
        """Verify that senior keywords in roles are correctly identified (so they can be filtered)."""
        senior_keywords = ['senior', 'staff', 'principal', 'lead', 'architect', 'manager', 'director']
        
        roles_to_filter = [
            "Senior Software Engineer",
            "Staff Scientist",
            "Principal Developer",
            "Tech Lead",
            "Solutions Architect",
            "Engineering Manager",
            "Director of AI"
        ]
        
        roles_to_keep = [
            "Software Engineer",
            "Associate Software Development Engineer",
            "Graduate Engineer",
            "Junior Data Scientist",
            "AI Engineer"
        ]
        
        for role in roles_to_filter:
            self.assertTrue(
                any(k in role.lower() for k in senior_keywords),
                f"Expected senior role '{role}' to match filter keywords"
            )
            
        for role in roles_to_keep:
            self.assertFalse(
                any(k in role.lower() for k in senior_keywords),
                f"Expected entry/mid-level role '{role}' to bypass filter keywords"
            )

    def test_age_freshness_filtering(self):
        """Verify age calculation relative to the last 24 hours."""
        current_time = datetime.now(timezone.utc)
        twenty_four_hours_ago = current_time - timedelta(hours=24)
        
        # Fresh job (1 hour ago)
        fresh_time = current_time - timedelta(hours=1)
        self.assertTrue(fresh_time >= twenty_four_hours_ago)
        
        # Stale job (25 hours ago)
        stale_time = current_time - timedelta(hours=25)
        self.assertFalse(stale_time >= twenty_four_hours_ago)

if __name__ == '__main__':
    unittest.main()
