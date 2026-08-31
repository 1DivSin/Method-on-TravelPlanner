"""Normalize psi-agent token logs and attribute full-chain Workflow usage."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


USAGE_MARKER = "SSE usage signal: "
PRIMARY_CASE = re.compile(r"case-(?P<case_id>[1-9][0-9]*)$")


def _optional_count(value: object, field: str) -> int | None:
    if value is None:
        return None
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative integer or null")
    return value


def _merge_optional(left: int | None, right: int | None) -> int | None:
    if left is None or right is None:
        return None
    return left + right


@dataclass(frozen=True)
class Usage:
    """One additive token ledger with explicit cache completeness."""

    model_calls: int = 0
    input_tokens: int | None = 0
    output_tokens: int | None = 0
    cache_read_input_tokens: int | None = 0
    cache_creation_input_tokens: int | None = 0

    def __post_init__(self) -> None:
        if type(self.model_calls) is not int or self.model_calls < 0:
            raise ValueError("model_calls must be a non-negative integer")
        for field in (
            "input_tokens",
            "output_tokens",
            "cache_read_input_tokens",
            "cache_creation_input_tokens",
        ):
            _optional_count(getattr(self, field), field)
        if (self.input_tokens is None) != (self.output_tokens is None):
            raise ValueError("input_tokens and output_tokens must both be known or both be null")
        if self.input_tokens is None and (
            self.cache_read_input_tokens is not None or self.cache_creation_input_tokens is not None
        ):
            raise ValueError("cache counts require known input_tokens")
        if self.input_tokens is not None:
            known_cache = (self.cache_read_input_tokens or 0) + (self.cache_creation_input_tokens or 0)
            if known_cache > self.input_tokens:
                raise ValueError("cache token breakdown exceeds input_tokens")

    @property
    def complete(self) -> bool:
        return self.input_tokens is not None

    @property
    def cache_complete(self) -> bool:
        return self.cache_read_input_tokens is not None and self.cache_creation_input_tokens is not None

    @property
    def uncached_input_tokens(self) -> int | None:
        if self.input_tokens is None or not self.cache_complete:
            return None
        return self.input_tokens - self.cache_read_input_tokens - self.cache_creation_input_tokens

    @property
    def processed_input_tokens(self) -> int | None:
        # psi-agent prompt_tokens and Claude modelUsage inputTokens both include
        # uncached input, cache reads, and cache creation for these experiments.
        return self.input_tokens

    @property
    def total_tokens(self) -> int | None:
        if self.input_tokens is None or self.output_tokens is None:
            return None
        return self.input_tokens + self.output_tokens

    def merged(self, other: Usage) -> Usage:
        complete = self.complete and other.complete
        return Usage(
            model_calls=self.model_calls + other.model_calls,
            input_tokens=(self.input_tokens + other.input_tokens if complete else None),
            output_tokens=(self.output_tokens + other.output_tokens if complete else None),
            cache_read_input_tokens=_merge_optional(
                self.cache_read_input_tokens,
                other.cache_read_input_tokens,
            ),
            cache_creation_input_tokens=_merge_optional(
                self.cache_creation_input_tokens,
                other.cache_creation_input_tokens,
            ),
        )

    def subtract(self, other: Usage) -> Usage:
        if not self.complete or not other.complete:
            return Usage(model_calls=max(0, self.model_calls - other.model_calls), input_tokens=None, output_tokens=None)
        fields = {
            "input_tokens": self.input_tokens - other.input_tokens,
            "output_tokens": self.output_tokens - other.output_tokens,
        }
        if min(fields.values()) < 0 or other.model_calls > self.model_calls:
            raise ValueError("cannot subtract a larger usage ledger")

        def difference(left: int | None, right: int | None) -> int | None:
            if left is None or right is None:
                return None
            if right > left:
                raise ValueError("cannot subtract a larger cache ledger")
            return left - right

        return Usage(
            model_calls=self.model_calls - other.model_calls,
            input_tokens=fields["input_tokens"],
            output_tokens=fields["output_tokens"],
            cache_read_input_tokens=difference(
                self.cache_read_input_tokens,
                other.cache_read_input_tokens,
            ),
            cache_creation_input_tokens=difference(
                self.cache_creation_input_tokens,
                other.cache_creation_input_tokens,
            ),
        )

    def to_dict(self) -> dict[str, int | bool | None]:
        return {
            "model_calls": self.model_calls,
            "input_tokens": self.input_tokens,
            "cache_read_input_tokens": self.cache_read_input_tokens,
            "cache_creation_input_tokens": self.cache_creation_input_tokens,
            "uncached_input_tokens": self.uncached_input_tokens,
            "processed_input_tokens": self.processed_input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "complete": self.complete,
            "cache_complete": self.cache_complete,
        }


def merge_usage(values: Iterable[Usage]) -> Usage:
    result = Usage()
    for value in values:
        result = result.merged(value)
    return result


def usage_from_mapping(data: dict[str, Any], *, calls_field: str = "model_calls") -> Usage:
    return Usage(
        model_calls=int(data.get(calls_field, 0)),
        input_tokens=_optional_count(data.get("input_tokens"), "input_tokens"),
        output_tokens=_optional_count(data.get("output_tokens"), "output_tokens"),
        cache_read_input_tokens=_optional_count(
            data.get("cached_input_tokens", data.get("cache_read_input_tokens")),
            "cache_read_input_tokens",
        ),
        cache_creation_input_tokens=_optional_count(
            data.get("cache_creation_input_tokens"),
            "cache_creation_input_tokens",
        ),
    )


def parse_psi_ai_log(path: Path) -> dict[str, Any]:
    usages: list[Usage] = []
    received = 0
    completed = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        received += "Received chat completion request" in line
        completed += "Request completed successfully" in line
        if USAGE_MARKER not in line:
            continue
        payload = json.loads(line.split(USAGE_MARKER, 1)[1])["psi_usage"]
        usages.append(
            Usage(
                model_calls=1,
                input_tokens=_optional_count(payload.get("prompt_tokens"), "prompt_tokens"),
                output_tokens=_optional_count(payload.get("completion_tokens"), "completion_tokens"),
                cache_read_input_tokens=_optional_count(
                    payload.get("cached_input_tokens"),
                    "cached_input_tokens",
                ),
                cache_creation_input_tokens=_optional_count(
                    payload.get("cache_creation_input_tokens"),
                    "cache_creation_input_tokens",
                ),
            )
        )
    observed = merge_usage(usages)
    coverage_complete = received == completed == len(usages)
    exact = observed if coverage_complete else Usage(
        model_calls=received,
        input_tokens=None,
        output_tokens=None,
        cache_read_input_tokens=None,
        cache_creation_input_tokens=None,
    )
    return {
        "usage": exact,
        "observed_usage": observed,
        "requests_received": received,
        "requests_completed": completed,
        "usage_signals": len(usages),
        "coverage_complete": coverage_complete,
    }


def _known_report_usage(data: dict[str, Any]) -> Usage:
    totals = data.get("totals")
    if not isinstance(totals, dict):
        raise ValueError("workflow token report has no totals object")
    if totals.get("input_tokens") is not None and totals.get("output_tokens") is not None:
        return usage_from_mapping(totals)
    steps = data.get("steps")
    if not isinstance(steps, list):
        raise ValueError("workflow token report has no steps array")
    known = [
        usage_from_mapping(step)
        for step in steps
        if isinstance(step, dict) and step.get("input_tokens") is not None and step.get("output_tokens") is not None
    ]
    return merge_usage(known)


def _file_bytes(paths: Iterable[Path]) -> int:
    return sum(path.stat().st_size for path in paths if path.is_file())


def _trace_sizes(workspace: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for path in sorted(workspace.glob("**/.psi/fusion-flow/session-runs/*/trace/*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        input_summary = data.get("input_summary")
        output_summary = data.get("output_summary")
        records.append(
            {
                "path": str(path),
                "label": data.get("label"),
                "status": data.get("status"),
                "input_summary_bytes": len(input_summary.encode()) if isinstance(input_summary, str) else 0,
                "output_summary_bytes": len(output_summary.encode()) if isinstance(output_summary, str) else 0,
            }
        )
    return {
        "count": len(records),
        "input_summary_bytes": sum(record["input_summary_bytes"] for record in records),
        "output_summary_bytes": sum(record["output_summary_bytes"] for record in records),
        "records": records,
    }


def analyze_psi_case(case_root: Path) -> dict[str, Any]:
    arm = case_root / "auto_workflow"
    full = parse_psi_ai_log(arm / "ai.log")
    report_records: list[dict[str, Any]] = []
    step_usages: list[dict[str, Any]] = []
    report_usages: list[Usage] = []
    reports = sorted((arm / "workspace").glob("**/runs/*/token-usage.json"))
    for path in reports:
        data = json.loads(path.read_text(encoding="utf-8"))
        usage = _known_report_usage(data)
        report_usages.append(usage)
        complete = data.get("complete") is True and data.get("totals", {}).get("complete") is True
        report_records.append(
            {
                "path": str(path),
                "run_id": data.get("run_id"),
                "workflow_id": data.get("workflow_id"),
                "status": data.get("status"),
                "reported_complete": complete,
                "usage": usage.to_dict(),
            }
        )
        for step in data.get("steps", []):
            if isinstance(step, dict):
                step_usages.append(
                    {
                        "run_id": data.get("run_id"),
                        "workflow_id": data.get("workflow_id"),
                        "step_id": step.get("step_id"),
                        "executor_id": step.get("executor_id"),
                        "executor_kind": step.get("executor_kind"),
                        "usage": usage_from_mapping(step).to_dict(),
                    }
                )
    observed_workflow = merge_usage(report_usages)
    reports_complete = bool(report_records) and all(
        record["reported_complete"] for record in report_records
    )
    workflow = observed_workflow if reports_complete else Usage(
        model_calls=observed_workflow.model_calls,
        input_tokens=None,
        output_tokens=None,
        cache_read_input_tokens=None,
        cache_creation_input_tokens=None,
    )
    full_chain_complete = full["coverage_complete"]
    attribution_complete = full_chain_complete and reports_complete
    outer = full["usage"].subtract(workflow) if attribution_complete else None
    workspace = arm / "workspace"
    artifacts = sorted(workspace.glob("**/runs/*/artifacts/*.md"))
    flow_sources = sorted(
        path
        for path in workspace.glob("**/*")
        if path.is_file() and path.suffix.lower() in {".g4", ".workflow"} and "runs" not in path.parts
    )
    primary_match = PRIMARY_CASE.fullmatch(case_root.name)
    return {
        "run_name": case_root.name,
        "case_id": int(primary_match.group("case_id")) if primary_match else None,
        "primary": primary_match is not None,
        "full_chain": full["usage"].to_dict(),
        "full_chain_observed": full["observed_usage"].to_dict(),
        "request_accounting": {
            key: value for key, value in full.items() if key not in {"usage", "observed_usage"}
        },
        "workflow_reported": workflow.to_dict(),
        "workflow_reported_observed": observed_workflow.to_dict(),
        "workflow_reports_complete": reports_complete,
        "full_chain_accounting_complete": full_chain_complete,
        "workflow_accounting_complete": reports_complete,
        "attribution_accounting_complete": attribution_complete,
        "outer_residual": outer.to_dict() if outer is not None else None,
        "workflow_run_count": len(report_records),
        "workflow_reports": report_records,
        "steps": step_usages,
        "artifact_file_count": len(artifacts),
        "artifact_bytes": _file_bytes(artifacts),
        "flow_source_file_count": len(flow_sources),
        "flow_source_bytes": _file_bytes(flow_sources),
        "traces": _trace_sizes(workspace),
    }


def load_run_map(path: Path) -> dict[int, str]:
    """Load and validate a case-id to canonical run-directory manifest."""

    data = json.loads(path.read_text(encoding="utf-8"))
    selections = data.get("selections")
    if not isinstance(selections, list) or not selections:
        raise ValueError("run map must contain a non-empty selections array")
    result: dict[int, str] = {}
    run_names: set[str] = set()
    for selection in selections:
        if not isinstance(selection, dict):
            raise ValueError("each run map selection must be an object")
        case_id = selection.get("case_id")
        run_name = selection.get("run_name")
        if type(case_id) is not int or case_id < 1:
            raise ValueError("run map case_id must be a positive integer")
        if not isinstance(run_name, str) or not run_name:
            raise ValueError("run map run_name must be a non-empty string")
        if case_id in result:
            raise ValueError(f"duplicate run map case_id: {case_id}")
        if run_name in run_names:
            raise ValueError(f"duplicate run map run_name: {run_name}")
        result[case_id] = run_name
        run_names.add(run_name)
    return result


def analyze_psi_run_root(
    run_root: Path,
    run_map: Mapping[int, str] | None = None,
) -> dict[str, Any]:
    runs = [analyze_psi_case(path) for path in sorted(run_root.glob("case-*")) if path.is_dir()]
    by_name = {run["run_name"]: run for run in runs}
    if run_map is None:
        canonical = [run for run in runs if run["primary"]]
        selected = {run["case_id"]: run["run_name"] for run in canonical}
    else:
        missing = sorted(set(run_map.values()) - set(by_name))
        if missing:
            raise ValueError(f"canonical run directories do not exist: {', '.join(missing)}")
        canonical = []
        selected = dict(sorted(run_map.items()))
        for case_id, run_name in selected.items():
            run = dict(by_name[run_name])
            run["case_id"] = case_id
            run["canonical"] = True
            canonical.append(run)
    canonical_names = {run["run_name"] for run in canonical}
    exact_full_chain = [run for run in canonical if run["full_chain_accounting_complete"]]
    exact_attribution = [run for run in canonical if run["attribution_accounting_complete"]]
    full_chain_total = merge_usage(
        usage_from_mapping(run["full_chain"]) for run in exact_full_chain
    )
    workflow_total = merge_usage(
        usage_from_mapping(run["workflow_reported"]) for run in exact_attribution
    )
    outer_total = merge_usage(
        usage_from_mapping(run["outer_residual"]) for run in exact_attribution
    )
    return {
        "schema_version": 2,
        "run_root": str(run_root.resolve()),
        "run_directory_count": len(runs),
        "canonical_run_map": {str(case_id): run_name for case_id, run_name in selected.items()},
        "canonical_case_count": len(canonical),
        "exact_full_chain_case_count": len(exact_full_chain),
        "incomplete_full_chain_case_ids": [
            run["case_id"] for run in canonical if not run["full_chain_accounting_complete"]
        ],
        "exact_attribution_case_count": len(exact_attribution),
        "incomplete_attribution_case_ids": [
            run["case_id"] for run in canonical if not run["attribution_accounting_complete"]
        ],
        "auxiliary_run_names": [run["run_name"] for run in runs if run["run_name"] not in canonical_names],
        "exact_full_chain_total": full_chain_total.to_dict(),
        "exact_workflow_total": workflow_total.to_dict(),
        "exact_outer_residual_total": outer_total.to_dict(),
        "workflow_run_count": sum(run["workflow_run_count"] for run in canonical),
        "artifact_bytes": sum(run["artifact_bytes"] for run in canonical),
        "trace_input_summary_bytes": sum(run["traces"]["input_summary_bytes"] for run in canonical),
        "trace_output_summary_bytes": sum(run["traces"]["output_summary_bytes"] for run in canonical),
        "runs": runs,
    }
