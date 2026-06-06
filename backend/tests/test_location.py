import unittest
from app.services.location import classify_location

class TestLocationClassifier(unittest.TestCase):
    def test_bangalore_classification(self):
        self.assertEqual(classify_location("Bangalore"), "BANGALORE")
        self.assertEqual(classify_location("Bengaluru"), "BANGALORE")
        self.assertEqual(classify_location("Bangalore, India"), "BANGALORE")
        self.assertEqual(classify_location("Bengaluru, Karnataka"), "BANGALORE")
        self.assertEqual(classify_location("Bangalore (Remote)"), "BANGALORE")

    def test_hyderabad_classification(self):
        self.assertEqual(classify_location("Hyderabad"), "HYDERABAD")
        self.assertEqual(classify_location("Hyderabad, India"), "HYDERABAD")
        self.assertEqual(classify_location("Hyderabad, Telangana"), "HYDERABAD")

    def test_remote_india_classification(self):
        self.assertEqual(classify_location("Remote (India)"), "REMOTE_INDIA")
        self.assertEqual(classify_location("India Remote"), "REMOTE_INDIA")
        self.assertEqual(classify_location("Remote, India"), "REMOTE_INDIA")

    def test_other_india_classification(self):
        self.assertEqual(classify_location("Pune, India"), "OTHER_INDIA")
        self.assertEqual(classify_location("Mumbai, India"), "OTHER_INDIA")
        self.assertEqual(classify_location("Delhi, India"), "OTHER_INDIA")

    def test_global_classification(self):
        self.assertEqual(classify_location("San Francisco, US"), "GLOBAL")
        self.assertEqual(classify_location("Singapore"), "GLOBAL")
        self.assertEqual(classify_location("London, UK"), "GLOBAL")
        self.assertEqual(classify_location("Sydney, Australia"), "GLOBAL")
        self.assertEqual(classify_location("Remote"), "GLOBAL")
        self.assertEqual(classify_location("Europe"), "GLOBAL")
        self.assertEqual(classify_location("US Remote"), "GLOBAL")

if __name__ == '__main__':
    unittest.main()
