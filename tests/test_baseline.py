import asyncio
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from travelplanner_experiment.protocol import Case, render_prompt
from travelplanner_experiment.tools import TravelPlannerTools
from travelplanner_experiment.workflow_io import WorkspaceIO


class BaselineTest(unittest.TestCase):
    def test_no_workflow_prompt_has_exact_case_identity(self):
        prompt = render_prompt(Case("7", 'Plan for "two".'), arm="no-workflow")
        self.assertIn('"idx": 7', prompt)
        self.assertIn('"query": "Plan for \\"two\\"."', prompt)

    def test_historical_workflow_variants_are_explicit(self):
        case = Case("1", "trip")
        self.assertTrue(render_prompt(case, arm="auto-workflow", variant="v1").startswith("Please complete"))
        self.assertIn("structured Artifact", render_prompt(case, arm="auto-workflow", variant="v2"))
        self.assertIn("validate again", render_prompt(case, arm="auto-workflow", variant="v3"))

    def test_tools_only_read_current_reference(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "reference.json"
            path.write_text(json.dumps([{"Description": "Restaurants in Austin", "Content": "all rows"}]))
            tools = TravelPlannerTools(path)
            self.assertEqual(asyncio.run(tools.search_restaurants("Austin")), "all rows")
            self.assertIn("no accommodations", asyncio.run(tools.search_accommodations("Austin")))

    def test_workspace_io_blocks_escape(self):
        with tempfile.TemporaryDirectory() as raw:
            io = WorkspaceIO(Path(raw))
            asyncio.run(io.write("flows/a.workflow", "flow a {}"))
            self.assertEqual(asyncio.run(io.read("flows/a.workflow")), "flow a {}")
            with self.assertRaises(ValueError):
                asyncio.run(io.read("../outside"))


if __name__ == "__main__":
    unittest.main()
