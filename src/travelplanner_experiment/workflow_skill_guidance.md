## Planning Contract

Before authoring G4 source, make the workflow plan explicit in the authoring
context. Identify the user's intent and success condition, every input and
output Artifact, each Step's single responsibility, information dependencies,
owned constraints, the quality gate and repair behavior, and concurrency,
timeout, retry, and budget limits.

Every constraint needs an owner: use a deterministic Program or graph check
when it is mechanically decidable, and an explicitly instructed Agent Step
when judgment is required. Fan out independent collection, keep dependent
selection and synthesis sequential, and join only when a consumer needs all
upstream results.

## Artifact Contracts

Artifacts are the data interface between Steps. When a downstream Step must
filter, sort, deduplicate, join, compare, calculate a budget, or check
membership, the upstream Artifact MUST preserve the required fields as
structured JSON values.

Define the top-level shape, required fields, field types, empty-result meaning,
source of each value, permitted transformations, and malformed-record behavior.
Do not use a long free-text or verbatim listing as the only representation for
data that a later Step must process mechanically. Agent Steps must submit their
declared Artifact with no prose mixed into the value.

## Quality Gates and Repair

Use a quality gate for candidate membership, budget, route/date, completeness,
safety/compliance, or exact-format constraints. A constrained planning flow
normally has this shape:

    collect/search -> filter/select -> assemble -> validate -> (repair -> validate)* -> output

Validation must consume the assembled result and relevant source Artifacts and
return structured, actionable failures. A failed report is not a successful
output. Repair only invalid selections or fields and validate again; do not
silently accept the first plan or rerun expensive collection when assembly-only
repair is sufficient. Record sampling, caps, filtering, and empty results so a
consumer can distinguish missing candidates from discarded candidates.
