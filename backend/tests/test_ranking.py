import unittest
from app.services.ranking import calculate_role_alignment, calculate_final_score

class TestRanking(unittest.TestCase):
    def test_calculate_role_alignment_sde1_entry_boost(self):
        """Verify that an entry-level keyword increases the role alignment score."""
        score = calculate_role_alignment(
            job_title="Software Engineer New Grad",
            user_category="SDE-1"
        )
        self.assertEqual(score, 100)

    def test_calculate_role_alignment_sde1_senior_penalty(self):
        """Verify that a senior keyword decreases the role alignment score for SDE-1."""
        score = calculate_role_alignment(
            job_title="Staff Software Engineer",
            user_category="SDE-1"
        )
        self.assertEqual(score, 35)

    def test_calculate_role_alignment_exact_match(self):
        """Verify that exact category matching scores maximum (before adjustments)."""
        score = calculate_role_alignment(
            job_title="Senior Software Engineer at Stripe",
            user_category="Senior Software Engineer"
        )
        self.assertEqual(score, 50)

    def test_calculate_final_score(self):
        """Verify the weighted scoring ranking formula."""
        score = calculate_final_score(
            skill_match=100,      # 45.0
            project_match=80,     # 20.0
            experience_match=70,  # 10.5
            education_match=60,   #  3.0
            role_alignment=90     #  9.0
        )                         # Total = 87.5 => rounded to 88
        self.assertEqual(score, 88)

if __name__ == '__main__':
    unittest.main()
