"""Shared attempt, retry, and token semantics for all experiment arms."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Iterable, Mapping


def _count(value: object, field: str) -> int | None:
    if value is None:
        return None
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative integer or null")
    return value


def _sum_known(values: Iterable[int | None]) -> int | None:
    items = list(values)
    if any(value is None for value in items):
        return None
    return sum(value for value in items if value is not None)


@dataclass(frozen=True)
class NormalizedUsage:
    """Provider-neutral token classes without treating unknown fields as zero."""

    model_calls: int
    uncached_input_tokens: int | None
    cache_read_input_tokens: int | None
    cache_creation_input_tokens: int | None
    output_tokens: int | None
    reported_cost_usd: float | None = None

    def __post_init__(self) -> None:
        if type(self.model_calls) is not int or self.model_calls < 0:
            raise ValueError("model_calls must be a non-negative integer")
        for field in (
            "uncached_input_tokens",
            "cache_read_input_tokens",
            "cache_creation_input_tokens",
            "output_tokens",
        ):
            _count(getattr(self, field), field)
        if self.reported_cost_usd is not None and self.reported_cost_usd < 0:
            raise ValueError("reported_cost_usd must be non-negative or null")

    @property
    def processed_input_tokens(self) -> int | None:
        return _sum_known(
            (
                self.uncached_input_tokens,
                self.cache_read_input_tokens,
                self.cache_creation_input_tokens,
            )
        )

    @property
    def total_tokens(self) -> int | None:
        processed = self.processed_input_tokens
        if processed is None or self.output_tokens is None:
            return None
        return processed + self.output_tokens

    @property
    def complete(self) -> bool:
        return self.processed_input_tokens is not None and self.output_tokens is not None

    def merged(self, other: NormalizedUsage) -> NormalizedUsage:
        costs = (self.reported_cost_usd, other.reported_cost_usd)
        return NormalizedUsage(
            model_calls=self.model_calls + other.model_calls,
            uncached_input_tokens=_sum_known(
                (self.uncached_input_tokens, other.uncached_input_tokens)
            ),
            cache_read_input_tokens=_sum_known(
                (self.cache_read_input_tokens, other.cache_read_input_tokens)
            ),
            cache_creation_input_tokens=_sum_known(
                (self.cache_creation_input_tokens, other.cache_creation_input_tokens)
            ),
            output_tokens=_sum_known((self.output_tokens, other.output_tokens)),
            reported_cost_usd=(
                sum(value for value in costs if value is not None)
                if all(value is not None for value in costs)
                else None
            ),
        )

    def to_dict(self) -> dict[str, int | float | bool | None]:
        return {
            "model_calls": self.model_calls,
            "uncached_input_tokens": self.uncached_input_tokens,
            "cache_read_input_tokens": self.cache_read_input_tokens,
            "cache_creation_input_tokens": self.cache_creation_input_tokens,
            "processed_input_tokens": self.processed_input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "reported_cost_usd": self.reported_cost_usd,
            "complete": self.complete,
        }


def usage_from_psi(
    *,
    model_calls: int,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    cached_input_tokens: int | None,
    cache_creation_input_tokens: int | None,
) -> NormalizedUsage:
    """Normalize psi usage, whose prompt count already includes all input classes."""

    processed = _count(prompt_tokens, "prompt_tokens")
    cached = _count(cached_input_tokens, "cached_input_tokens")
    created = _count(cache_creation_input_tokens, "cache_creation_input_tokens")
    if processed is None or cached is None or created is None:
        uncached = None
    else:
        uncached = processed - cached - created
        if uncached < 0:
            raise ValueError("psi cache breakdown exceeds prompt_tokens")
    return NormalizedUsage(
        model_calls=model_calls,
        uncached_input_tokens=uncached,
        cache_read_input_tokens=cached,
        cache_creation_input_tokens=created,
        output_tokens=_count(completion_tokens, "completion_tokens"),
    )


def usage_from_claude_model_usage(
    model_usage: Mapping[str, Mapping[str, Any]],
    *,
    reported_cost_usd: float | None = None,
) -> NormalizedUsage:
    """Normalize Claude Code modelUsage, where inputTokens means uncached input."""

    models = list(model_usage.values())
    if not models:
        return NormalizedUsage(0, None, None, None, None, reported_cost_usd)

    def total(field: str) -> int | None:
        return _sum_known(_count(model.get(field), field) for model in models)

    return NormalizedUsage(
        model_calls=0,
        uncached_input_tokens=total("inputTokens"),
        cache_read_input_tokens=total("cacheReadInputTokens"),
        cache_creation_input_tokens=total("cacheCreationInputTokens"),
        output_tokens=total("outputTokens"),
        reported_cost_usd=reported_cost_usd,
    )


class FailureKind(StrEnum):
    NETWORK = "network"
    RATE_LIMIT = "rate_limit"
    UPSTREAM_5XX = "upstream_5xx"
    PROCESS_INFRASTRUCTURE = "process_infrastructure"
    TIMEOUT_WITH_USAGE = "timeout_with_usage"
    OUTPUT_CONTRACT = "output_contract"
    WORKFLOW = "workflow"
    VALIDATOR = "validator"
    EVALUATOR_QUALITY = "evaluator_quality"
    UNKNOWN = "unknown"


_NETWORK_MARKERS = (
    "connection reset",
    "connection refused",
    "connection aborted",
    "cannot connect",
    "failed to connect",
    "name or service not known",
    "temporary failure in name resolution",
    "tls handshake",
    "server disconnected",
)
_PROCESS_MARKERS = (
    "socket did not appear",
    "broken pipe",
    "process exited",
    "nonzero exit",
    "worker crashed",
)


def classify_failure(
    error: str,
    *,
    http_status: int | None = None,
    usage_observed: bool = False,
) -> FailureKind:
    """Classify an attempt without conflating quality failures with infrastructure."""

    text = error.casefold()
    if http_status == 429 or "rate limit" in text or "quota" in text:
        return FailureKind.RATE_LIMIT
    if http_status is not None and 500 <= http_status <= 599:
        return FailureKind.UPSTREAM_5XX
    if any(marker in text for marker in _NETWORK_MARKERS):
        return FailureKind.NETWORK
    if "timeout" in text or "timed out" in text:
        return FailureKind.TIMEOUT_WITH_USAGE if usage_observed else FailureKind.PROCESS_INFRASTRUCTURE
    if "output contract" in text or "json extraction" in text or "invalid result json" in text:
        return FailureKind.OUTPUT_CONTRACT
    if "validate_travel_plan" in text or "second validation" in text:
        return FailureKind.VALIDATOR
    if "workflow" in text and any(
        marker in text for marker in ("compile", "parse", "step", "artifact", "run_flow")
    ):
        return FailureKind.WORKFLOW
    if "evaluator" in text or "final pass" in text or "constraint" in text:
        return FailureKind.EVALUATOR_QUALITY
    if any(marker in text for marker in _PROCESS_MARKERS):
        return FailureKind.PROCESS_INFRASTRUCTURE
    return FailureKind.UNKNOWN


RETRYABLE_FAILURES = frozenset(
    {
        FailureKind.NETWORK,
        FailureKind.RATE_LIMIT,
        FailureKind.UPSTREAM_5XX,
        FailureKind.PROCESS_INFRASTRUCTURE,
    }
)


@dataclass(frozen=True)
class Attempt:
    attempt: int
    status: str
    failure_kind: FailureKind | None
    usage: NormalizedUsage
    output_path: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == "success" and self.failure_kind is None

    @property
    def retryable(self) -> bool:
        return self.failure_kind in RETRYABLE_FAILURES


def select_canonical_attempt(attempts: Iterable[Attempt]) -> Attempt | None:
    """Select the first successful output; failed attempts remain billable."""

    ordered = sorted(attempts, key=lambda attempt: attempt.attempt)
    return next((attempt for attempt in ordered if attempt.succeeded), None)


def billed_usage(attempts: Iterable[Attempt]) -> NormalizedUsage:
    """Aggregate every API attempt, including retry attempts that produced no output."""

    result = NormalizedUsage(0, 0, 0, 0, 0, 0.0)
    for attempt in attempts:
        result = result.merged(attempt.usage)
    return result
