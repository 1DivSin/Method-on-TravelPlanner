import hashlib
import tempfile
import unittest
from pathlib import Path

from travelplanner_experiment import Case, load_cases, render_prompt, select_cases


class TravelPlannerContractTest(unittest.TestCase):
    def test_common_prompt_preserves_case_identity_and_query(self):
        case = Case(7, 'Plan for "two" without rewriting this query.')
        prompt = render_prompt(case)

        self.assertIn('"idx": 7', prompt)
        self.assertIn('Plan for "two" without rewriting this query.', prompt)
        self.assertIn('"query": "Plan for \\"two\\" without rewriting this query."', prompt)

    def test_registered_common_prompt_bytes_do_not_drift(self):
        prompt = render_prompt(Case(7, "Plan for two.")).encode("utf-8")

        self.assertEqual(len(prompt), 1500)
        self.assertEqual(
            hashlib.sha256(prompt).hexdigest(),
            "b48b9a4caeba791e1c31fb319202f8b1c5d56107e54d2a741a129714d6aaf40a",
        )

    def test_loader_validates_only_frozen_prompt_row_schema(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "prompts.jsonl"
            path.write_text(
                '{"idx":2,"query":"second","unused_metadata":{"domain":"frozen"}}\n'
                '{"idx":1,"query":"first"}\n',
                encoding="utf-8",
            )
            cases = load_cases(path)

        self.assertEqual(select_cases(cases, (1, 2)), (Case(1, "first"), Case(2, "second")))


if __name__ == "__main__":
    unittest.main()
