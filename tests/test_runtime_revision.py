import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from travelplanner_experiment.protocol import Case, render_prompt
from travelplanner_experiment.runtime import (
    V6_BASE_RUNTIME,
    V6_PROTOCOL_DEDUP_RUNTIME,
    runtime_revision,
)


class RuntimeRevisionTest(unittest.TestCase):
    def test_layer_four_changes_runtime_without_changing_prompt(self):
        case = Case("17", "Plan and validate a trip.")
        previous = render_prompt(
            case, arm="auto-workflow", variant="v6-min-03-conditional-repair"
        )
        treated = render_prompt(
            case, arm="auto-workflow", variant="v6-min-04-step-protocol-dedup"
        )

        self.assertEqual(treated, previous)
        self.assertEqual(runtime_revision("v6-min-03-conditional-repair"), V6_BASE_RUNTIME)
        self.assertEqual(
            runtime_revision("v6-min-04-step-protocol-dedup"), V6_PROTOCOL_DEDUP_RUNTIME
        )

    def test_runtime_patch_matches_registered_hash_and_commit(self):
        root = Path(__file__).parents[1]
        patch = root / V6_PROTOCOL_DEDUP_RUNTIME.patch
        content = patch.read_bytes()

        self.assertEqual(hashlib.sha256(content).hexdigest(), V6_PROTOCOL_DEDUP_RUNTIME.patch_sha256)
        self.assertTrue(
            content.startswith(f"From {V6_PROTOCOL_DEDUP_RUNTIME.commit} ".encode()),
            content[:80],
        )


if __name__ == "__main__":
    unittest.main()
