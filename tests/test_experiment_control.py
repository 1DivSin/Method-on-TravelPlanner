import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from travelplanner_experiment.experiment_control import (
    Attempt,
    FailureKind,
    NormalizedUsage,
    billed_usage,
    classify_failure,
    select_canonical_attempt,
    usage_from_claude_model_usage,
    usage_from_psi,
)


class ExperimentControlTest(unittest.TestCase):
    def test_psi_prompt_tokens_are_already_processed_input(self):
        usage = usage_from_psi(
            model_calls=2,
            prompt_tokens=100,
            completion_tokens=7,
            cached_input_tokens=70,
            cache_creation_input_tokens=10,
        )
        self.assertEqual(usage.uncached_input_tokens, 20)
        self.assertEqual(usage.processed_input_tokens, 100)

    def test_claude_input_tokens_are_uncached_and_processed_adds_cache(self):
        usage = usage_from_claude_model_usage(
            {
                "opus": {
                    "inputTokens": 20,
                    "cacheReadInputTokens": 70,
                    "cacheCreationInputTokens": 10,
                    "outputTokens": 7,
                },
                "sonnet": {
                    "inputTokens": 2,
                    "cacheReadInputTokens": 6,
                    "cacheCreationInputTokens": 1,
                    "outputTokens": 1,
                },
            }
        )
        self.assertEqual(usage.uncached_input_tokens, 22)
        self.assertEqual(usage.processed_input_tokens, 109)
        self.assertEqual(usage.output_tokens, 8)

    def test_missing_cache_field_remains_unknown(self):
        usage = usage_from_claude_model_usage(
            {"opus": {"inputTokens": 20, "cacheReadInputTokens": 70, "outputTokens": 7}}
        )
        self.assertIsNone(usage.cache_creation_input_tokens)
        self.assertIsNone(usage.processed_input_tokens)
        self.assertFalse(usage.complete)

    def test_only_infrastructure_failures_retry(self):
        self.assertEqual(classify_failure("HTTP 503", http_status=503), FailureKind.UPSTREAM_5XX)
        self.assertEqual(classify_failure("plan JSON extraction failed"), FailureKind.OUTPUT_CONTRACT)
        self.assertEqual(
            classify_failure("timed out", usage_observed=True),
            FailureKind.TIMEOUT_WITH_USAGE,
        )

    def test_canonical_output_and_billing_are_separate(self):
        failed = Attempt(
            1,
            "failed",
            FailureKind.NETWORK,
            NormalizedUsage(1, 3, 4, 1, 2, 0.1),
        )
        success = Attempt(2, "success", None, NormalizedUsage(1, 5, 6, 2, 3, 0.2), "answer.json")
        self.assertEqual(select_canonical_attempt([failed, success]), success)
        billed = billed_usage([failed, success])
        self.assertEqual(billed.processed_input_tokens, 21)
        self.assertEqual(billed.output_tokens, 5)
        self.assertAlmostEqual(billed.reported_cost_usd, 0.3)


if __name__ == "__main__":
    unittest.main()
