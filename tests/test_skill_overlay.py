import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from travelplanner_experiment.skill_overlay import apply_workflow_skill_guidance


class SkillOverlayTest(unittest.TestCase):
    def test_inserts_contract_once_and_preserves_frontmatter(self):
        source = "---\nname: workflow\n---\n\n# Workflow\n\nIntro.\n\n## Intent Routing\n\nRoutes.\n"
        updated = apply_workflow_skill_guidance(source)
        self.assertTrue(updated.startswith("---\nname: workflow\n---"))
        self.assertIn("## Planning Contract", updated)
        self.assertIn("## Artifact Contracts", updated)
        self.assertIn("## Quality Gates and Repair", updated)
        self.assertLess(updated.index("## Planning Contract"), updated.index("## Intent Routing"))
        self.assertEqual(apply_workflow_skill_guidance(updated), updated)

    def test_requires_workflow_heading(self):
        with self.assertRaisesRegex(ValueError, "# Workflow"):
            apply_workflow_skill_guidance("# Different skill")


if __name__ == "__main__":
    unittest.main()
