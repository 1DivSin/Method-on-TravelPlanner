"""Frozen loader for registered TravelPlanner prompt rows."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from workflow_experiment.selection import read_jsonl, select_by_id

from .protocol import Case


def load_cases(path: Path) -> tuple[Case, ...]:
    cases: list[Case] = []
    for line_number, row in enumerate(read_jsonl(path), 1):
        case_id = row.get("idx")
        query = row.get("query")
        if type(case_id) is not int or case_id < 1:
            raise ValueError(f"{path}:{line_number}: idx must be a positive integer")
        if not isinstance(query, str) or not query:
            raise ValueError(f"{path}:{line_number}: query must be a non-empty string")
        cases.append(Case(case_id=case_id, query=query))
    if len({case.case_id for case in cases}) != len(cases):
        raise ValueError(f"{path}: case identifiers must be unique")
    return tuple(cases)


def select_cases(cases: Iterable[Case], case_ids: Iterable[int]) -> tuple[Case, ...]:
    return select_by_id(cases, case_ids, key=lambda case: case.case_id)
