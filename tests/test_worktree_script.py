import subprocess
import unittest
from pathlib import Path


class WorktreeScriptTest(unittest.TestCase):
    def test_rejects_unscoped_branch_name_without_fetching(self):
        script = Path(__file__).parents[1] / "scripts" / "new-worktree.sh"
        result = subprocess.run(
            ["bash", str(script), "bad branch"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("branch must match", result.stderr)


if __name__ == "__main__":
    unittest.main()
