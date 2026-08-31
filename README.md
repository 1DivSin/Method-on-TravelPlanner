# Method-on-TravelPlanner

This repository contains the reviewable implementation increments used by the
TravelPlanner dynamic-workflow experiments. The code is intentionally split
into stacked pull requests so prompt, accuracy, and token-cost changes can be
reviewed and measured independently.

## Baseline harness

The baseline provides:

- the byte-stable TravelPlanner JSON output contract;
- isolated access to the current case's official reference information;
- workspace-confined read/write helpers for Workflow authoring;
- opt-in historical v1-v3 prompt treatments;
- unit tests that do not call a model or the official evaluator.

Run the tests with:

```bash
python -m unittest discover -s tests -v
```

Later stacked PRs add one treatment at a time. No API credentials, benchmark
database, generated sessions, or model outputs are committed with this harness.

## Clean v6 experiment baseline

The `v6-token-efficient` treatment records the prompt, typed candidate tools,
deterministic validator, and executable Artifact-contract runtime patch used by
the accepted v6 configuration. Its psi-agent runtime is pinned to
`54f55089b036badd1c56c57fff68190bbc34086d`.

This baseline deliberately excludes cache/token accounting changes, case
selection, generated model sessions, evaluator results, and rejected treatment
records. Later stacked PRs change one registered treatment at a time.
