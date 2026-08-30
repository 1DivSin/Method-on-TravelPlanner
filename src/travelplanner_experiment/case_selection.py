"""Validate and select aligned TravelPlanner manifest and prompt rows."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


REQUIRED_METADATA = frozenset(
    {
        "org",
        "dest",
        "days",
        "date",
        "people_number",
        "budget",
        "local_constraint",
        "visiting_city_number",
    }
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: row must be an object")
        rows.append(value)
    if not rows:
        raise ValueError(f"{path}: no rows")
    return rows


def validate_manifest_row(row: dict[str, Any], *, line_number: int) -> int:
    case_id = row.get("case_id")
    if not isinstance(case_id, (str, int)) or not str(case_id).isdigit():
        raise ValueError(f"manifest row {line_number}: case_id must be a positive integer string")
    numeric_id = int(case_id)
    if numeric_id < 1:
        raise ValueError(f"manifest row {line_number}: case_id must be positive")
    if not isinstance(row.get("question"), str) or not row["question"].strip():
        raise ValueError(f"manifest row {line_number}: question must be non-empty")
    metadata = row.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError(f"manifest row {line_number}: metadata must be an object")
    if isinstance(metadata.get("metadata"), dict):
        raise ValueError(
            f"manifest row {line_number}: metadata is nested; the normalized manifest was likely prepared twice"
        )
    missing = sorted(REQUIRED_METADATA - set(metadata))
    if missing:
        raise ValueError(f"manifest row {line_number}: metadata is missing {missing}")
    return numeric_id


def parse_case_ids(value: str) -> list[int]:
    result: list[int] = []
    seen: set[int] = set()
    for component in value.split(","):
        component = component.strip()
        if not component:
            continue
        if "-" in component:
            start_text, end_text = component.split("-", 1)
            start, end = int(start_text), int(end_text)
            if start > end:
                raise ValueError(f"descending case range: {component}")
            values: Iterable[int] = range(start, end + 1)
        else:
            values = (int(component),)
        for case_id in values:
            if case_id < 1:
                raise ValueError("case IDs must be positive")
            if case_id in seen:
                raise ValueError(f"duplicate case ID: {case_id}")
            seen.add(case_id)
            result.append(case_id)
    if not result:
        raise ValueError("no case IDs selected")
    return result


def select_aligned_cases(
    manifest_rows: list[dict[str, Any]],
    prompt_rows: list[dict[str, Any]],
    case_ids: list[int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    manifest_by_id: dict[int, dict[str, Any]] = {}
    for line_number, row in enumerate(manifest_rows, 1):
        case_id = validate_manifest_row(row, line_number=line_number)
        if case_id in manifest_by_id:
            raise ValueError(f"duplicate manifest case ID: {case_id}")
        manifest_by_id[case_id] = row

    prompt_by_id: dict[int, dict[str, Any]] = {}
    for line_number, row in enumerate(prompt_rows, 1):
        idx = row.get("idx")
        if type(idx) is not int or idx < 1:
            raise ValueError(f"prompt row {line_number}: idx must be a positive integer")
        if not isinstance(row.get("query"), str) or not row["query"].strip():
            raise ValueError(f"prompt row {line_number}: query must be non-empty")
        if idx in prompt_by_id:
            raise ValueError(f"duplicate prompt idx: {idx}")
        prompt_by_id[idx] = row

    missing_manifest = [case_id for case_id in case_ids if case_id not in manifest_by_id]
    missing_prompts = [case_id for case_id in case_ids if case_id not in prompt_by_id]
    if missing_manifest or missing_prompts:
        raise ValueError(
            f"missing selected rows: manifest={missing_manifest}, prompts={missing_prompts}"
        )
    return (
        [manifest_by_id[case_id] for case_id in case_ids],
        [prompt_by_id[case_id] for case_id in case_ids],
    )


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> str:
    encoded = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(encoded, encoding="utf-8")
    return hashlib.sha256(encoded.encode()).hexdigest()
