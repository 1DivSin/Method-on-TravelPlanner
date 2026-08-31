"""Deterministic, content-blind selection of pre-registered records."""

from __future__ import annotations

import json
from collections.abc import Callable, Hashable, Iterable, Mapping
from pathlib import Path
from typing import Any, TypeVar


Record = dict[str, Any]
T = TypeVar("T")
Identifier = TypeVar("Identifier", bound=Hashable)


def read_jsonl(path: Path) -> tuple[Record, ...]:
    """Read non-empty JSON object rows without applying domain policy."""

    rows: list[Record] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: row must be a JSON object")
        rows.append(value)
    if not rows:
        raise ValueError(f"{path}: no JSON object rows")
    return tuple(rows)


def select_by_id(
    records: Iterable[T],
    selected_ids: Iterable[Identifier],
    *,
    key: Callable[[T], Identifier],
) -> tuple[T, ...]:
    """Return records in pre-registered order without inspecting their content."""

    requested = tuple(selected_ids)
    if not requested:
        raise ValueError("at least one identifier must be selected")
    if len(set(requested)) != len(requested):
        raise ValueError("selected identifiers must be unique")

    indexed: dict[Identifier, T] = {}
    for record in records:
        identifier = key(record)
        if identifier in indexed:
            raise ValueError(f"duplicate source identifier: {identifier!r}")
        indexed[identifier] = record

    missing = [identifier for identifier in requested if identifier not in indexed]
    if missing:
        raise ValueError(f"selected identifiers are missing from source: {missing!r}")
    return tuple(indexed[identifier] for identifier in requested)


def canonical_jsonl(rows: Iterable[Mapping[str, Any]]) -> bytes:
    """Serialize rows deterministically for hashing and frozen experiment input."""

    encoded = (
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    )
    return "".join(encoded).encode("utf-8")
