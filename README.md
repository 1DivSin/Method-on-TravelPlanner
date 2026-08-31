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

## Workflow skill contract

The first treatment overlays general planning, structured Artifact, quality
gate, and repair guidance onto the isolated Workflow skill copy. The overlay is
idempotent and preserves the source skill frontmatter. It is deliberately
domain-neutral: TravelPlanner-specific prompt and tool changes come later.

## v4 CC Dynamic prompt carrier

The v4 prompt adopts the bounded Claude Code Dynamic Workflow carrier: no more
than three phases, five Agent Steps, and five tool calls per Step; one fallback
for an empty query; and a ten-minute end-to-end budget. The TravelPlanner task,
field rules, and JSON output contract remain byte-equivalent to the baseline.

## v5 accuracy: typed candidates and lodging filters

The first v5 accuracy change replaces raw candidate tables with compact typed
JSON. Lodging candidates are rejected before selection when minimum nights,
occupancy, room type, or house rules cannot satisfy the query. The result keeps
filter counts so an empty source can be distinguished from filtered candidates.

## v5 accuracy: deterministic validation and repair

The second accuracy change adds `validate_travel_plan` as a structured quality
gate. A failed report drives one targeted assembly repair using the original
typed candidates, followed by one revalidation. Prose-only self-review is not
accepted as validation, and a second failure produces the empty-plan contract.

## Valid empty references

TravelPlanner reference rows use two representations: an array when candidates
exist, and a human-readable string when a valid query has no candidates. The
typed adapter now maps those strings to an empty candidate result with
`availability: "none"`, while reserving `availability: "missing"` for an absent
reference key. Unexpected object or scalar shapes still fail closed.

## Executable Workflow Artifact contracts

The psi-agent runtime patch in
`patches/psi-agent/0001-enforce-workflow-artifact-contracts.patch` makes Artifact
format, JSON type, and semantic descriptions executable rather than advisory.
Contracts can be declared in FusionFlow line/block comments or in inline and
external-file `step_instruction` text:

```fusionflow
-- @artifact flights [array]: Preserve flight_number, price, departure_time, and arrival_time; [] means no matches.

step_instruction(search_step) == "Search the exact route.\n@artifact flights [array]: Preserve canonical fields.";
```

The runtime validates workflow and Step boundaries, injects descriptions into
Agent/Human/Program contexts, and constrains Agent result submission with JSON
Schema. Supported top-level types are `null`, `boolean`, `integer`, `number`,
`string`, `object`, and `array`.

The patch applies to `1DivSin/psi-agent` at base commit
`545fbc73c70ba7fe6360a63d90ed4bedc8e9d181` and includes its focused regression
suite. Apply it from a checkout of that commit with:

```bash
git am /path/to/Method-on-TravelPlanner/patches/psi-agent/0001-enforce-workflow-artifact-contracts.patch
```
