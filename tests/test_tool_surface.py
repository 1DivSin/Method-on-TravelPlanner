import tempfile
import unittest
from pathlib import Path

from workflow_experiment.tool_surface import freeze_external_tool_surface


class ToolSurfaceTest(unittest.TestCase):
    def test_freezes_external_document_tool_without_wrapping_it(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            adapter = root / "adapter.py"
            schema = root / "schema.json"
            adapter.write_text("def extract(path): return path\n", encoding="utf-8")
            schema.write_text('{"extract":{"path":"string"}}\n', encoding="utf-8")

            surface = freeze_external_tool_surface(
                revision="abc123",
                adapter_path=adapter,
                schema_path=schema,
                visible_tools=("extract",),
            )

            self.assertEqual(surface.visible_tools, ("extract",))
            self.assertEqual(surface.adapter.size_bytes, len(adapter.read_bytes()))
            self.assertEqual(len(surface.schema.sha256), 64)

    def test_rejects_duplicate_tool_names(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            adapter = root / "adapter"
            schema = root / "schema"
            adapter.write_bytes(b"implementation")
            schema.write_bytes(b"schema")
            with self.assertRaisesRegex(ValueError, "unique"):
                freeze_external_tool_surface(
                    revision="revision",
                    adapter_path=adapter,
                    schema_path=schema,
                    visible_tools=("read", "read"),
                )


if __name__ == "__main__":
    unittest.main()
