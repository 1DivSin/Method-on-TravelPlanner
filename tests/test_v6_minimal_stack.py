import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from travelplanner_experiment.protocol import (
    Case,
    V6_CONDITIONAL_REPAIR_TREATMENT,
    V6_QUIET_AUTHORING_TREATMENT,
    V6_SINGLE_CONSUMER_SEARCH_TREATMENT,
    render_prompt,
)


class V6MinimalStackTest(unittest.TestCase):
    def test_quiet_authoring_is_an_isolated_registered_treatment(self):
        case = Case("17", "Plan a trip without exposing authoring narration.")
        baseline = render_prompt(case, arm="auto-workflow", variant="v6-token-efficient")
        treated = render_prompt(case, arm="auto-workflow", variant="v6-min-01-quiet-authoring")

        expected = baseline.replace(
            "Please complete", V6_QUIET_AUTHORING_TREATMENT + "Please complete", 1
        )
        self.assertEqual(treated, expected)
        self.assertNotIn(V6_QUIET_AUTHORING_TREATMENT, baseline)
        self.assertIn("Perform every authoring and static-check operation in full", treated)

    def test_quiet_authoring_does_not_change_no_workflow_arm(self):
        case = Case("17", "Plan a trip.")
        self.assertEqual(
            render_prompt(case, arm="no-workflow", variant="v6-token-efficient"),
            render_prompt(case, arm="no-workflow", variant="v6-min-01-quiet-authoring"),
        )

    def test_single_consumer_search_builds_only_on_quiet_authoring(self):
        case = Case("17", "Plan a trip from the official candidates.")
        previous = render_prompt(case, arm="auto-workflow", variant="v6-min-01-quiet-authoring")
        treated = render_prompt(
            case, arm="auto-workflow", variant="v6-min-02-single-consumer-search"
        )

        expected = previous.replace(
            "Please complete", V6_SINGLE_CONSUMER_SEARCH_TREATMENT + "Please complete", 1
        )
        self.assertEqual(treated, expected)
        self.assertEqual(treated.count(V6_QUIET_AUTHORING_TREATMENT), 1)
        self.assertEqual(treated.count(V6_SINGLE_CONSUMER_SEARCH_TREATMENT), 1)
        self.assertIn("Preserve the complete source candidates", treated)
        self.assertIn("separate compact derived Artifact", treated)

    def test_conditional_repair_builds_only_on_single_consumer_treatment(self):
        case = Case("17", "Plan and validate a trip.")
        previous = render_prompt(
            case, arm="auto-workflow", variant="v6-min-02-single-consumer-search"
        )
        treated = render_prompt(
            case, arm="auto-workflow", variant="v6-min-03-conditional-repair"
        )

        expected = previous.replace(
            "Please complete", V6_CONDITIONAL_REPAIR_TREATMENT + "Please complete", 1
        )
        self.assertEqual(treated, expected)
        self.assertEqual(treated.count(V6_CONDITIONAL_REPAIR_TREATMENT), 1)
        self.assertIn("When `valid` is true, submit that exact object immediately and stop", treated)
        self.assertIn("Only when `valid` is false", treated)
        self.assertIn("validate once more", treated)


if __name__ == "__main__":
    unittest.main()
