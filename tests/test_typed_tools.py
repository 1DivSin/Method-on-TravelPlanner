import asyncio
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from travelplanner_experiment.protocol import Case, render_prompt
from travelplanner_experiment.typed_tools import TypedTravelPlannerTools


class TypedToolsTest(unittest.TestCase):
    def _tools(self, root: Path) -> TypedTravelPlannerTools:
        data = {
            "Accommodations in B": [
                {"NAME": "Too long", "city": "B", "price": 80, "room type": "Entire home/apt", "house_rules": "No smoking", "minimum nights": 3, "maximum occupancy": 2},
                {"NAME": "Valid", "city": "B", "price": 100, "room type": "Entire home/apt", "house_rules": "No parties", "minimum nights": 2, "maximum occupancy": 2},
            ],
            "Flight from A to B on 2022-03-01": [{"Flight Number": "F1", "Price": 10, "DepTime": "09:00", "ArrTime": "10:00", "FlightDate": "2022-03-01", "OriginCityName": "A", "DestCityName": "B", "Distance": 100}],
        }
        path = root / "structured.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return TypedTravelPlannerTools(path)

    def test_accommodation_filters_before_selection(self):
        with tempfile.TemporaryDirectory() as raw:
            result = json.loads(asyncio.run(self._tools(Path(raw)).search_accommodations("B", 2, 3, "entire room", "")))
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["candidates"][0]["name"], "Valid")
        self.assertEqual(result["candidates"][0]["rooms_required"], 2)
        self.assertEqual(result["filter"]["rejected_counts"]["minimum_nights"], 1)

    def test_flights_use_canonical_fields(self):
        with tempfile.TemporaryDirectory() as raw:
            result = json.loads(asyncio.run(self._tools(Path(raw)).search_flights("A", "B", "2022-03-01")))
        self.assertEqual(result["candidates"][0]["flight_number"], "F1")
        self.assertNotIn("Flight Number", result["candidates"][0])

    def test_no_result_strings_are_structured_empty_results(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "structured.json"
            path.write_text(
                json.dumps(
                    {
                        "Flight from A to B on d1": "There is no flight from A to B on d1",
                        "Accommodations in B": "There is no accommodation in B",
                        "Restaurants in B": "There is no restaurant in B",
                        "Attractions in B": "There is no attraction in B",
                    }
                ),
                encoding="utf-8",
            )
            tools = TypedTravelPlannerTools(path)
            results = [
                json.loads(asyncio.run(tools.search_flights("A", "B", "d1"))),
                json.loads(asyncio.run(tools.search_accommodations("B"))),
                json.loads(asyncio.run(tools.search_restaurants("B"))),
                json.loads(asyncio.run(tools.search_attractions("B"))),
            ]
        self.assertEqual([result["availability"] for result in results], ["none"] * 4)
        for result in results:
            self.assertEqual(result["candidate_count"], 0)
            self.assertEqual(result["candidates"], [])
            self.assertIn("message", result)

    def test_missing_reference_is_explicit_and_non_fatal(self):
        with tempfile.TemporaryDirectory() as raw:
            result = json.loads(asyncio.run(self._tools(Path(raw)).search_restaurants("Unknown")))
        self.assertEqual(result["availability"], "missing")
        self.assertEqual(result["candidate_count"], 0)
        self.assertEqual(result["candidates"], [])
        self.assertNotIn("message", result)

    def test_invalid_reference_type_fails_closed(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "structured.json"
            path.write_text(json.dumps({"Restaurants in B": {"Name": "not-a-list"}}), encoding="utf-8")
            tools = TypedTravelPlannerTools(path)
            with self.assertRaisesRegex(ValueError, "array or no-result string"):
                asyncio.run(tools.search_restaurants("B"))

    def test_prompt_registers_only_candidate_treatment(self):
        prompt = render_prompt(Case("1", "trip"), arm="auto-workflow", variant="v5-typed-candidates")
        self.assertIn("canonical source fields", prompt)
        self.assertNotIn("validate_travel_plan", prompt)


if __name__ == "__main__":
    unittest.main()
