#!/usr/bin/env python3
"""Build a full-chain/Workflow/outer token ledger from saved psi-agent runs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from travelplanner_experiment.token_accounting import analyze_psi_run_root, load_run_map


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root", type=Path)
    parser.add_argument("--run-map", type=Path, help="explicit case-to-run canonical selection")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    run_map = load_run_map(args.run_map) if args.run_map is not None else None
    report = analyze_psi_run_root(args.run_root, run_map)
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
