import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from travelplanner_experiment.protocol import Case, render_prompt
from travelplanner_experiment.validator import TravelPlanValidator


class ValidatorTest(unittest.TestCase):
    def _validator(self, root: Path) -> TravelPlanValidator:
        reference = {
            "Restaurants in B": [{"Name": f"R{i}", "City": "B", "Average Cost": 10} for i in range(1, 7)],
            "Accommodations in B": [{"NAME": "Hotel", "city": "B", "price": 100, "minimum nights": 2, "maximum occupancy": 2}],
            "Flight from A to B on d1": [{"Flight Number": "F1", "Price": 100}],
            "Flight from B to A on d3": [{"Flight Number": "F2", "Price": 100}],
        }
        constraints = {"days": 3, "people_number": 2, "budget": 2000}
        ref = root / "reference.json"
        con = root / "constraints.json"
        ref.write_text(json.dumps(reference), encoding="utf-8")
        con.write_text(json.dumps(constraints), encoding="utf-8")
        return TravelPlanValidator(ref, con)

    def _plan(self):
        return {"idx": 1, "query": "trip", "plan": [
            {"day": 1, "current_city": "from A to B", "transportation": "Flight Number: F1, from A to B", "breakfast": "-", "attraction": "-", "lunch": "R1, B", "dinner": "R2, B", "accommodation": "Hotel, B"},
            {"day": 2, "current_city": "B", "transportation": "-", "breakfast": "R3, B", "attraction": "-", "lunch": "R4, B", "dinner": "R5, B", "accommodation": "Hotel, B"},
            {"day": 3, "current_city": "from B to A", "transportation": "Flight Number: F2, from B to A", "breakfast": "R6, B", "attraction": "-", "lunch": "-", "dinner": "-", "accommodation": "-"},
        ]}

    def test_accepts_member_plan_and_rejects_duplicate(self):
        with tempfile.TemporaryDirectory() as raw:
            validator = self._validator(Path(raw))
            plan = self._plan()
            good = json.loads(validator.validate(json.dumps(plan)))
            plan["plan"][1]["lunch"] = "R3, B"
            bad = json.loads(validator.validate(json.dumps(plan)))
        self.assertTrue(good["valid"], good)
        self.assertFalse(bad["valid"])
        self.assertTrue(any(v["constraint"] == "diversity.restaurant" for v in bad["violations"]))

    def test_no_result_reference_is_skipped_by_membership_index(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            reference = {
                "Restaurants in B": "There is no restaurant in B",
                "Accommodations in B": "There is no accommodation in B",
                "Flight from A to B on d1": "There is no flight from A to B on d1",
            }
            constraints = {"days": 1, "people_number": 1, "budget": 100}
            ref = root / "reference.json"
            con = root / "constraints.json"
            ref.write_text(json.dumps(reference), encoding="utf-8")
            con.write_text(json.dumps(constraints), encoding="utf-8")
            validator = TravelPlanValidator(ref, con)
            result = json.loads(
                validator.validate(
                    json.dumps(
                        {
                            "idx": 1,
                            "query": "trip",
                            "plan": [
                                {
                                    "day": 1,
                                    "current_city": "B",
                                    "transportation": "-",
                                    "breakfast": "-",
                                    "attraction": "-",
                                    "lunch": "-",
                                    "dinner": "-",
                                    "accommodation": "-",
                                }
                            ],
                        }
                    )
                )
            )
        self.assertTrue(result["valid"], result)

    def test_prompt_requires_tool_validation_and_one_repair(self):
        prompt = render_prompt(Case("1", "trip"), arm="auto-workflow", variant="v5-validated")
        self.assertIn("validate_travel_plan", prompt)
        self.assertIn("repair only reported fields", prompt)
        self.assertIn("validate once more", prompt)

    def test_token_efficient_prompt_colocates_final_planning_and_validation(self):
        prompt = render_prompt(Case("1", "trip"), arm="auto-workflow", variant="v6-token-efficient")
        self.assertIn("one final planning Agent Step", prompt)
        self.assertIn("call `validate_travel_plan`", prompt)
        self.assertIn("submit the exact validated object unchanged", prompt)
        self.assertIn("validate exactly once more", prompt)
        self.assertIn("Do not create separate selection, assembly, validator", prompt)
        self.assertIn("exactly these eight keys and no others", prompt)
        self.assertIn("`days` and every other extra or misspelled key are forbidden", prompt)
        self.assertIn("delete the old key, not merely add the corrected key", prompt)
        self.assertIn('`allowed_tool(agent, "search_flights");`', prompt)
        self.assertIn("declare every Step and Agent as separate constants", prompt)
        self.assertIn("Never combine Step and Agent types", prompt)
        self.assertIn('`{"idx": <case idx>, "query": <exact original query>, "plan": []}`', prompt)
        self.assertIn("Never submit placeholder or fabricated day entries", prompt)
        self.assertIn("no collector may lock in the final cities or route", prompt)
        self.assertIn("the single final planning Agent alone selects the cities and route", prompt)
        self.assertIn("Never select a city with empty required lodging, restaurant, or attraction candidates", prompt)
        self.assertIn("copy it verbatim into `transportation`", prompt)
        self.assertIn("Never summarize or reconstruct a ground-transport string", prompt)
        self.assertIn("origin to the first city, all inter-city legs, and the last city back to origin", prompt)
        self.assertIn("this requirement includes both origin endpoint legs", prompt)
        self.assertIn("Never put a partial route in the feasible-routes Artifact", prompt)


if __name__ == "__main__":
    unittest.main()
