import asyncio
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from travelplanner_experiment.protocol import Case, render_prompt
from travelplanner_experiment.typed_tools import TypedTravelPlannerTools


class StepBoundaryTest(unittest.TestCase):
    def _reference(self, root: Path) -> Path:
        path = root / "reference.json"
        path.write_text(json.dumps({"Flight from A to B on d": [{"Flight Number": "F1"}]}), encoding="utf-8")
        return path

    def test_outer_session_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            tools = TypedTravelPlannerTools(
                self._reference(Path(raw)), session_id="outer-session", workflow_step_only=True
            )
            with self.assertRaisesRegex(PermissionError, "Agent Steps inside run_flow"):
                asyncio.run(tools.search_flights("A", "B", "d"))

    def test_workflow_step_can_query_same_tool(self):
        with tempfile.TemporaryDirectory() as raw:
            tools = TypedTravelPlannerTools(
                self._reference(Path(raw)), session_id="", workflow_step_only=True
            )
            result = json.loads(asyncio.run(tools.search_flights("A", "B", "d")))
        self.assertEqual(result["candidates"][0]["flight_number"], "F1")

    def test_final_v5_prompt_composes_four_treatments(self):
        prompt = render_prompt(Case("1", "trip"), arm="auto-workflow", variant="v5")
        self.assertIn("canonical source fields", prompt)
        self.assertIn("validate_travel_plan", prompt)
        self.assertIn("SKILL.md` exactly once", prompt)
        self.assertIn("MUST NOT call TravelPlanner data tools", prompt)


if __name__ == "__main__":
    unittest.main()
