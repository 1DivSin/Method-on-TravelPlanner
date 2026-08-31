import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from travelplanner_experiment.token_accounting import (
    Usage,
    analyze_psi_case,
    analyze_psi_run_root,
    load_run_map,
    parse_psi_ai_log,
)


class TokenAccountingTest(unittest.TestCase):
    def test_usage_preserves_unknown_cache_counts(self):
        usage = Usage(model_calls=1, input_tokens=10, output_tokens=2, cache_read_input_tokens=None, cache_creation_input_tokens=None)
        self.assertIsNone(usage.uncached_input_tokens)
        self.assertFalse(usage.cache_complete)
        merged = usage.merged(Usage(model_calls=1, input_tokens=5, output_tokens=1))
        self.assertEqual(merged.input_tokens, 15)
        self.assertIsNone(merged.cache_read_input_tokens)

    def test_usage_subtraction_keeps_cache_breakdown(self):
        full = Usage(3, 100, 20, 70, 10)
        inner = Usage(2, 60, 12, 40, 8)
        self.assertEqual(
            full.subtract(inner).to_dict(),
            Usage(1, 40, 8, 30, 2).to_dict(),
        )

    def test_parse_psi_log_requires_request_usage_completion_parity(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "ai.log"
            payload = {
                "psi_usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 3,
                    "cached_input_tokens": 6,
                    "cache_creation_input_tokens": 2,
                }
            }
            path.write_text(
                "Received chat completion request\n"
                f"SSE usage signal: {json.dumps(payload)}\n"
                "Request completed successfully\n",
                encoding="utf-8",
            )
            report = parse_psi_ai_log(path)
        self.assertTrue(report["coverage_complete"])
        self.assertEqual(report["usage"].uncached_input_tokens, 2)

    def test_parse_psi_log_preserves_partial_observations_without_claiming_exact_usage(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "ai.log"
            path.write_text("Received chat completion request\n", encoding="utf-8")
            report = parse_psi_ai_log(path)
        self.assertFalse(report["coverage_complete"])
        self.assertFalse(report["usage"].complete)
        self.assertTrue(report["observed_usage"].complete)
        self.assertEqual(report["observed_usage"].input_tokens, 0)

    def test_case_attributes_complete_workflow_from_full_chain(self):
        with tempfile.TemporaryDirectory() as raw:
            case = Path(raw) / "case-7"
            arm = case / "auto_workflow"
            report_dir = arm / "workspace" / "7" / "attempt-1" / "flows" / "x" / "runs" / "run"
            report_dir.mkdir(parents=True)
            payloads = [
                {"prompt_tokens": 70, "completion_tokens": 8, "cached_input_tokens": 50, "cache_creation_input_tokens": 10},
                {"prompt_tokens": 30, "completion_tokens": 4, "cached_input_tokens": 20, "cache_creation_input_tokens": 5},
            ]
            (arm / "ai.log").write_text(
                "".join(
                    "Received chat completion request\n"
                    f"SSE usage signal: {json.dumps({'psi_usage': payload})}\n"
                    "Request completed successfully\n"
                    for payload in payloads
                ),
                encoding="utf-8",
            )
            token_report = {
                "complete": True,
                "run_id": "run",
                "workflow_id": "x",
                "status": "completed",
                "totals": {
                    "complete": True,
                    "model_calls": 1,
                    "input_tokens": 70,
                    "output_tokens": 8,
                    "cached_input_tokens": 50,
                    "cache_creation_input_tokens": 10,
                },
                "steps": [],
            }
            (report_dir / "token-usage.json").write_text(json.dumps(token_report), encoding="utf-8")
            result = analyze_psi_case(case)
        self.assertEqual(result["outer_residual"]["input_tokens"], 30)
        self.assertEqual(result["outer_residual"]["output_tokens"], 4)
        self.assertEqual(result["outer_residual"]["uncached_input_tokens"], 5)

    def test_run_map_selects_canonical_rerun_and_audits_other_directories(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_complete_case(root / "case-1", 10, 2)
            self._write_complete_case(root / "case-1-final", 20, 3)
            result = analyze_psi_run_root(root, {1: "case-1-final"})
        self.assertEqual(result["canonical_run_map"], {"1": "case-1-final"})
        self.assertEqual(result["exact_full_chain_case_count"], 1)
        self.assertEqual(result["exact_attribution_case_count"], 1)
        self.assertEqual(result["exact_full_chain_total"]["input_tokens"], 20)
        self.assertEqual(result["auxiliary_run_names"], ["case-1"])

    def test_load_run_map_rejects_duplicate_cases(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "map.json"
            path.write_text(
                json.dumps(
                    {
                        "selections": [
                            {"case_id": 1, "run_name": "case-1"},
                            {"case_id": 1, "run_name": "case-1-final"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate run map case_id"):
                load_run_map(path)

    @staticmethod
    def _write_complete_case(case: Path, input_tokens: int, output_tokens: int) -> None:
        arm = case / "auto_workflow"
        report_dir = arm / "workspace" / "flows" / "x" / "runs" / "run"
        report_dir.mkdir(parents=True)
        payload = {
            "prompt_tokens": input_tokens,
            "completion_tokens": output_tokens,
            "cached_input_tokens": 0,
            "cache_creation_input_tokens": 0,
        }
        (arm / "ai.log").write_text(
            "Received chat completion request\n"
            f"SSE usage signal: {json.dumps({'psi_usage': payload})}\n"
            "Request completed successfully\n",
            encoding="utf-8",
        )
        (report_dir / "token-usage.json").write_text(
            json.dumps(
                {
                    "complete": True,
                    "run_id": "run",
                    "workflow_id": "x",
                    "status": "completed",
                    "totals": {
                        "complete": True,
                        "model_calls": 1,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "cached_input_tokens": 0,
                        "cache_creation_input_tokens": 0,
                    },
                    "steps": [],
                }
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
