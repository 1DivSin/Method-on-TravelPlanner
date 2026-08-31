import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from travelplanner_experiment.case_selection import (
    parse_case_ids,
    select_aligned_cases,
    validate_manifest_row,
)


def manifest_row(case_id: int) -> dict[str, object]:
    return {
        "case_id": str(case_id),
        "question": f"question {case_id}",
        "metadata": {
            "org": "A",
            "dest": "B",
            "days": "3",
            "date": "2022-01-01",
            "people_number": "1",
            "budget": "1000",
            "local_constraint": "{}",
            "visiting_city_number": "1",
        },
    }


class CaseSelectionTest(unittest.TestCase):
    def test_parse_case_ids_preserves_registered_order(self):
        self.assertEqual(parse_case_ids("3,1,5-6"), [3, 1, 5, 6])

    def test_rejects_manifest_prepared_twice(self):
        row = manifest_row(1)
        row["metadata"] = {"metadata": row["metadata"]}
        with self.assertRaisesRegex(ValueError, "prepared twice"):
            validate_manifest_row(row, line_number=1)

    def test_selects_manifest_and_prompts_in_identical_requested_order(self):
        manifest = [manifest_row(1), manifest_row(2)]
        prompts = [
            {"idx": 1, "query": "prompt 1"},
            {"idx": 2, "query": "prompt 2"},
        ]
        selected_manifest, selected_prompts = select_aligned_cases(
            manifest, prompts, [2, 1]
        )
        self.assertEqual([row["case_id"] for row in selected_manifest], ["2", "1"])
        self.assertEqual([row["idx"] for row in selected_prompts], [2, 1])


if __name__ == "__main__":
    unittest.main()
