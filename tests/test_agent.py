import unittest

from app.agent import analyze_issue


class TestAnalyzeIssue(unittest.TestCase):
    def test_returns_priority_and_severity_fields(self):
        result = analyze_issue('Motor is overheating and making noise', 'Industrial Motor')

        self.assertIn('severity', result)
        self.assertIn('priority_score', result)
        self.assertIn('possible_causes', result)
        self.assertIn('recommended_actions', result)

        self.assertIn(result['severity'], {'Critical', 'High', 'Medium', 'Low'})
        self.assertGreaterEqual(result['priority_score'], 1)
        self.assertLessEqual(result['priority_score'], 100)

    def test_uses_english_only_processing(self):
        result = analyze_issue('موٹر گرم ہے اور شور کر رہی ہے', 'Industrial Motor')

        self.assertIn('language', result)
        self.assertEqual(result['language'], 'en')
        self.assertIn('issue_summary', result)
        self.assertTrue(result['issue_summary'])

    def test_distinguishes_different_machine_faults(self):
        overheating = analyze_issue('Motor is overheating and making noise', 'Industrial Motor')
        vibration = analyze_issue('Motor is vibrating heavily and misaligned', 'Industrial Motor')

        self.assertNotEqual(
            overheating['matches'][0].get('Fault / Incident'),
            vibration['matches'][0].get('Fault / Incident')
        )
        self.assertIn('Overheating', overheating['matches'][0].get('Fault / Incident', ''))
        self.assertIn('Excessive Vibration', vibration['matches'][0].get('Fault / Incident', ''))

    def test_matches_machine_name_and_issue_together_for_water_motor_fire_case(self):
        result = analyze_issue('pani wali motor ko aag lag gai aur overheating ho rahi hai', 'pani wali motor')

        self.assertTrue(result['matches'])
        self.assertIn('Water Pump', result['matches'][0].get('Machine', ''))
        self.assertIn('Overheating', result['matches'][0].get('Fault / Incident', ''))
        self.assertGreaterEqual(result['priority_score'], 80)


if __name__ == '__main__':
    unittest.main()
