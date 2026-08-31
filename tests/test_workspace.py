import tempfile
import unittest
from pathlib import Path

from workflow_experiment.workspace import WorkspaceFiles


class WorkspaceFilesTest(unittest.TestCase):
    def test_confines_build_artifacts_to_one_workspace(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = WorkspaceFiles(Path(raw))
            digest = workspace.write_text("reports/lint.txt", "clean\n")

            self.assertEqual(workspace.read_text("reports/lint.txt"), "clean\n")
            self.assertEqual(digest.name, "reports/lint.txt")
            with self.assertRaisesRegex(ValueError, "inside"):
                workspace.read_text("../outside.txt")

    def test_rejects_symlink_escape(self):
        with tempfile.TemporaryDirectory() as raw, tempfile.TemporaryDirectory() as outside:
            root = Path(raw)
            (root / "external").symlink_to(Path(outside), target_is_directory=True)
            workspace = WorkspaceFiles(root)
            with self.assertRaisesRegex(ValueError, "inside"):
                workspace.write_text("external/result.txt", "not allowed")


if __name__ == "__main__":
    unittest.main()
