import asyncio
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from travelplanner_experiment.protocol import Case, render_prompt
from travelplanner_experiment.workflow_io import WorkspaceIO


class ReadOnceTest(unittest.TestCase):
    def test_aliases_share_read_once_key_and_first_read_is_atomic(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            primary = root / "skills/workflow/SKILL.md"
            alias = root / "skills/workflow-skill/SKILL.md"
            primary.parent.mkdir(parents=True)
            alias.parent.mkdir(parents=True)
            primary.write_text("complete skill", encoding="utf-8")
            alias.write_text("complete skill", encoding="utf-8")
            io = WorkspaceIO(root, read_once_references=True)
            first = asyncio.run(io.read("skills/workflow/SKILL.md", offset=999, limit=1))
            second = asyncio.run(io.read("skills/workflow-skill/SKILL.md"))
        self.assertEqual(first, "complete skill")
        self.assertIn("Already loaded", second)

    def test_unrelated_files_keep_normal_ranges(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "notes.txt").write_text("one\ntwo\nthree\n", encoding="utf-8")
            io = WorkspaceIO(root, read_once_references=True)
            self.assertEqual(asyncio.run(io.read("notes.txt", offset=1, limit=1)), "two\n")
            self.assertEqual(asyncio.run(io.read("notes.txt", offset=1, limit=1)), "two\n")

    def test_prompt_records_read_once_contract(self):
        prompt = render_prompt(Case("1", "trip"), arm="auto-workflow", variant="v5-read-once")
        self.assertIn("SKILL.md` exactly once", prompt)
        self.assertIn("workflow-skill` alias", prompt)


if __name__ == "__main__":
    unittest.main()
