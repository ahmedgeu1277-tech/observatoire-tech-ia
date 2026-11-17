import unittest

from auto_amelioration import ALLOWED_CHECKS, build_improvement_report


class ContinuousImprovementTests(unittest.TestCase):
    def test_all_checks_passed(self):
        report = build_improvement_report([
            {"name": name, "status": "passed", "return_code": 0}
            for name in ALLOWED_CHECKS
        ])
        self.assertEqual(report["status"], "checks_passed")
        self.assertTrue(report["autonomy"]["synthetic_user_testing"])
        self.assertFalse(report["autonomy"]["automatic_production_code_changes"])

    def test_failed_test_creates_critical_backlog_item(self):
        report = build_improvement_report([
            {"name": "python_tests", "status": "failed", "return_code": 1}
        ])
        self.assertEqual(report["status"], "needs_attention")
        self.assertEqual(report["improvement_backlog"][0]["priority"], "critical")
        self.assertFalse(report["improvement_backlog"][0]["automatic_code_change"])

    def test_unknown_check_is_rejected(self):
        with self.assertRaises(ValueError):
            build_improvement_report([{"name": "rm_everything", "status": "passed"}])


if __name__ == "__main__":
    unittest.main()
