#!/usr/bin/env python3
"""Create byte-audited, aligned TravelPlanner manifest and prompt subsets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from travelplanner_experiment.case_selection import (
    parse_case_ids,
    read_jsonl,
    select_aligned_cases,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--prompts", type=Path, required=True)
    parser.add_argument("--case-ids", required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    parser.add_argument("--output-prompts", type=Path, required=True)
    args = parser.parse_args()

    case_ids = parse_case_ids(args.case_ids)
    manifest, prompts = select_aligned_cases(
        read_jsonl(args.manifest),
        read_jsonl(args.prompts),
        case_ids,
    )
    manifest_hash = write_jsonl(args.output_manifest, manifest)
    prompt_hash = write_jsonl(args.output_prompts, prompts)
    print(
        json.dumps(
            {
                "case_ids": case_ids,
                "case_count": len(case_ids),
                "manifest_sha256": manifest_hash,
                "prompts_sha256": prompt_hash,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
