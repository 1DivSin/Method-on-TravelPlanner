import json
import unittest

from workflow_experiment.provenance import ArtifactDigest, create_manifest, sha256_bytes


class ProvenanceTest(unittest.TestCase):
    def test_build_manifest_is_stable_for_build_pipeline_inputs(self):
        source = ArtifactDigest.from_bytes("source-tree", b"revision-17")
        catalog = ArtifactDigest.from_bytes("operator-catalog", b"agent(name) -> result")

        first = create_manifest(
            configuration={"model": "fixed-model", "case_ids": ["lint", "unit"]},
            artifacts=(source, catalog),
        )
        second = create_manifest(
            configuration={"case_ids": ["lint", "unit"], "model": "fixed-model"},
            artifacts=(catalog, source),
        )

        self.assertEqual(first, second)
        self.assertEqual(len(sha256_bytes(first)), 64)
        self.assertEqual(json.loads(first)["artifacts"][0]["name"], "operator-catalog")

    def test_manifest_rejects_ambiguous_artifact_names(self):
        artifact = ArtifactDigest.from_bytes("input", b"one")
        with self.assertRaisesRegex(ValueError, "unique"):
            create_manifest(configuration={}, artifacts=(artifact, artifact))


if __name__ == "__main__":
    unittest.main()
