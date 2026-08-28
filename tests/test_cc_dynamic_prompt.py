import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from travelplanner_experiment.protocol import Case, CC_DYNAMIC_WORKFLOW_PROMPT_TEMPLATE, render_prompt


class CcDynamicPromptTest(unittest.TestCase):
    def test_v4_renders_cc_dynamic_carrier(self):
        case = Case("7", 'Plan for "two".')
        prompt = render_prompt(case, arm="auto-workflow", variant="v4")
        expected = CC_DYNAMIC_WORKFLOW_PROMPT_TEMPLATE.format(
            idx="7", query=case.query, query_json=json.dumps(case.query)
        )
        self.assertEqual(prompt, expected)
        self.assertIn("at most 5 Agent Steps", prompt)
        self.assertIn("at most 5 tool calls", prompt)
        self.assertIn("within 10 minutes", prompt)

    def test_no_workflow_is_unchanged_by_v4_name(self):
        case = Case("7", "trip")
        self.assertEqual(
            render_prompt(case, arm="no-workflow", variant="v1"),
            render_prompt(case, arm="no-workflow", variant="v4"),
        )


if __name__ == "__main__":
    unittest.main()
