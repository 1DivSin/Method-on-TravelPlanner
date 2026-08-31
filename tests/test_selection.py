import json
import tempfile
import unittest
from pathlib import Path

from workflow_experiment.selection import canonical_jsonl, read_jsonl, select_by_id


class SelectionTest(unittest.TestCase):
    def test_selects_preregistered_document_jobs_in_declared_order(self):
        jobs = (
            {"job_id": "extract", "document": "invoice.pdf"},
            {"job_id": "review", "document": "contract.md"},
            {"job_id": "publish", "document": "release.txt"},
        )

        selected = select_by_id(jobs, ("publish", "extract"), key=lambda row: row["job_id"])

        self.assertEqual([row["job_id"] for row in selected], ["publish", "extract"])

    def test_rejects_duplicate_or_missing_identifiers(self):
        rows = ({"id": "a"}, {"id": "b"})
        with self.assertRaisesRegex(ValueError, "unique"):
            select_by_id(rows, ("a", "a"), key=lambda row: row["id"])
        with self.assertRaisesRegex(ValueError, "missing"):
            select_by_id(rows, ("c",), key=lambda row: row["id"])

    def test_jsonl_round_trip_is_deterministic(self):
        rows = ({"z": 1, "a": "alpha"}, {"a": "beta", "z": 2})
        encoded = canonical_jsonl(rows)
        self.assertEqual(encoded, b'{"a":"alpha","z":1}\n{"a":"beta","z":2}\n')
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "jobs.jsonl"
            path.write_bytes(encoded)
            self.assertEqual(
                read_jsonl(path),
                tuple(json.loads(line) for line in encoded.splitlines()),
            )


if __name__ == "__main__":
    unittest.main()
