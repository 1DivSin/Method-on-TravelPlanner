# Method-on-TravelPlanner

This branch contains neutral experiment plumbing for reproducible Workflow
comparisons. It intentionally contains no TravelPlanner solver, candidate
filter, validator, repair policy, runtime patch, or benchmark-local Workflow
Skill overlay.

## Method hypothesis

A harness that selects only pre-registered case identities, freezes the exact
input bytes and external dependencies, records deterministic provenance, and
isolates each workspace makes Workflow experiments reproducible in any domain
without changing how the task is solved.

The generic implementation lives in `src/workflow_experiment/`. Its tests use
document-processing and build-pipeline examples rather than TravelPlanner.
`src/travelplanner_experiment/` is limited to the frozen benchmark case schema
and the common task/output contract.

## Frozen harness contract

Every comparison arm must receive the same rendered task contract and the same
official data tools. A treatment activation belongs in a separate,
pre-registered commit so it remains the only arm difference.

The repository does not reimplement the official tool adapter. Before a run,
the caller must register the external adapter revision, adapter file hash,
schema file hash, and ordered visible tool names with
`freeze_external_tool_surface`. The resulting surface record must be identical
for every arm.

The following historical treatments are deliberately absent:

- v2-v6 prompt variants and authoring syntax instructions;
- typed or filtered candidate tools;
- model-visible validation, repair, retry, or fallback behavior;
- read-once Skill and grammar special cases;
- benchmark-local Skill overlays and psi-agent runtime patches;
- result-aware case selection and historical token-log parsing.

The official evaluator belongs after final output collection. Its result must
not select retries, amend prompts, or alter an acceptance path.

## Current experiment environment

The `experiment/` directory is a frozen TravelPlanner runner snapshot used by
the maintained experiment root. It contains the preregistered 30-case inputs,
prompt template, task-tool adapters, provenance-producing runner, and
post-inference evaluator snapshot preparation scripts. Generated runs,
credentials, and evaluator outputs are intentionally kept out of this source
tree. See `docs/CURRENT_EXPERIMENT.md` for the exact hashes and baseline
commit required to execute it.

## Verification

Run the domain-neutral and benchmark-contract unit tests with:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

No test calls a model, an external tool, or the official evaluator.
