# TravelPlanner Workflow Method Cleanup Handoff

Date: 2026-08-31

This document is the handoff for rebuilding the TravelPlanner experiment and
moving admissible Workflow-method changes into `psi-agent`. It is intended to
be self-contained: do not rely on the prior chat when making branch, PR, or
implementation decisions.

## 1. Objective and mandatory research rule

Rebuild the experiment so that every treatment improves the general Workflow
method rather than encoding TravelPlanner-specific solver behavior.

The workspace-wide rule is in:

```text
/public/home/sychen/cxy/workflow/AGENTS.md
```

The decisive counterfactual is:

> If TravelPlanner and all of its domain vocabulary were removed, would this
> exact change still improve the Workflow method on an unrelated task?

If the answer is no, uncertain, or depends on benchmark traces or evaluator
feedback, the change must not be implemented, committed, pushed, or included
in a new experiment.

In particular:

- `src/travelplanner_experiment/` is an experiment/harness ownership boundary,
  not a valid home for Workflow method improvements.
- Benchmark-local solver prompts, filters, validators, repair policies,
  fallback rules, graph shapes, or tool policies are prohibited.
- A method change belongs in the production Workflow Skill, runtime, scheduler,
  Artifact transport, grammar/catalog documentation, or protocol in
  `psi-agent`.
- Every method change needs at least one non-TravelPlanner test.
- Do not use benchmark results, failed cases, evaluator output, or per-case
  traces to choose a prompt rule, retry, graph amendment, or acceptance path.

## 2. Repositories and frozen historical versions

Method repository/worktrees:

```text
repository: /public/home/sychen/cxy/workflow/.staging/Method-on-TravelPlanner
remote:     https://github.com/1DivSin/Method-on-TravelPlanner.git

v6 historical worktree:
/public/home/sychen/cxy/workflow/method-wt-v6-clean
branch: experiment/v6-clean-20260830
commit: bfc7d5645c8ea4ac49d81306b9f3ae16ccf55536
```

The branch name `experiment/v6-clean-20260830` is historical terminology. The
branch is not methodologically clean; it contains TravelPlanner-specific prompt,
typed-tool, validator, and Artifact-contract treatments.

The psi-agent version used by the previous 30-case run was:

```text
worktree: /public/home/sychen/cxy/workflow/psi-agent-wt-v6-protocol-standalone
commit:   54f55089b036badd1c56c57fff68190bbc34086d
```

The candidate production psi-agent baseline before the experiment-specific
patches and token-accounting stack is:

```text
a9579c7d4f544be24efd59dcb6ef0c3a07e48863
```

The previous 30-case result must retain its exact provenance. Do not rewrite,
rebase, or relabel the historical branches as if they represented the proposed
clean experiment.

## 3. Current branch topology

The Method repository is not one linear stack:

```text
origin/main: c8dece2
|
+-- feature/00-travelplanner-harness: 960d1da
|   |
|   +-- feature/01 -> 02 -> 03 -> 04 -> 05 -> 06 -> chore/07
|   |
|   +-- experiment/v6-clean-20260830: bfc7d56
|       +-- exp/v6-min-01 -> 02 -> 03 -> 04
|
+-- experiment/workflow-token-four-arm-v1: df6007e
|   (starts from a content-equivalent but different harness commit, 1af4ca5)
|
+-- review/workflow-capabilities-v1: a6f03d8
|   (starts from another content-equivalent harness commit, c9c2c03)
|
+-- travelplanner-results-20260827: b2525fc
```

`experiment/workflow-token-four-arm-v1` and
`review/workflow-capabilities-v1` have exactly the same final Git tree:

```text
a47b747fa4c391172a335b0d1759936f0e619fad
```

The review branch only repackages the four-arm branch's 30 commits into 12
commits. It is not a cleaner implementation.

## 4. PR disposition

No PR was closed, merged, rebased, or edited during this audit. The recommended
disposition is:

| PR | Head branch | Disposition | Reason |
| --- | --- | --- | --- |
| #1 | `travelplanner-results-20260827` | Archive as historical results | Preserve raw results and hashes; analysis must not drive new method rules. |
| #2 | `feature/00-travelplanner-harness` | Supersede, do not merge directly | Useful harness pieces are mixed with `WORKFLOW_V2/V3` treatments. |
| #3 | `feature/01-workflow-skill-contract` | Close/supersede | Benchmark-local Skill overlay; only a rewritten domain-neutral hypothesis may move to psi-agent. |
| #4 | `feature/02-cc-dynamic-prompt` | Close/supersede | TravelPlanner prompt carrier and fixed task-specific limits. |
| #5 | `feature/03-typed-candidate-filtering` | Close/supersede | Changes candidate set and encodes lodging constraints. |
| #6 | `feature/04-deterministic-validation-repair` | Close/supersede | TravelPlanner evaluator/domain knowledge controls execution. |
| #7 | `feature/05-read-once-references` | Close/supersede | Benchmark-local context/tool-call policy changes behavior and token cost. |
| #8 | `feature/06-workflow-step-tool-boundary` | Close/supersede | TravelPlanner-only tool visibility restriction changes the comparison surface. |
| #9 | `chore/07-pr-workflow-policy` | Rebuild independently from `main` if still wanted | Process rule is useful but currently depends on the rejected stack. |
| #10 | `fix/typed-reference-artifact-contracts` | Archive/close | Prefix of the four-arm treatment line; mixes typed references and runtime patch. |
| #11 | `experiment/workflow-token-four-arm-v1` | Drop from development line; retain immutable historical ref | Almost entirely obsolete/ad hoc treatment plus historical evidence. |
| #12 | `review/workflow-capabilities-v1` | Drop from development line; retain immutable historical ref | Final tree is identical to #11. |
| #13-#16 | `exp/v6-min-*` | Do not consider; close or mark superseded | User explicitly excluded these benchmark-local changes. |

"Drop" means: do not merge, do not make it an ancestor of the new canonical
line, and do not cherry-pick its commits. Retain a remote branch or archival tag
until the historical results and provenance have been copied to their final
read-only location. Do not delete remote refs as part of the initial cleanup.

## 5. Four-arm branch audit

Branch:

```text
experiment/workflow-token-four-arm-v1
commit: df6007ea249eb4d01a24318b2ec9272b60c8081e
30 commits after origin/main
```

The branch should not contribute code to the new canonical line.

### Do not migrate

- TravelPlanner v4/v5/v6 prompt contracts.
- Typed candidate conversion and pre-filtering.
- TravelPlanner deterministic validator and repair/fallback behavior.
- Benchmark-local Artifact-contract patch.
- Read-once reference policy and tool-visibility treatments.
- The seven result-driven v6 prompt amendments:
  - exact final plan keys;
  - pinned authoring syntax;
  - literal empty-plan fallback;
  - multi-city viability selection;
  - complete route candidates;
  - runtime agent configuration;
  - canonical query copying.
- `token_accounting.py`; cache/token collection already exists in psi-agent and
  this implementation is coupled to historical logs and run directories.
- `experiment_control.py` as code; its failure classifier contains
  TravelPlanner validator/evaluator markers.
- `case_selection.py` as code; it requires TravelPlanner metadata and prompt
  fields.
- The G3 case set as a new evaluation set; it was selected from the union of a
  prior token subset and known baseline failures.

### Preserve only as historical evidence

- `experiments/20260831-four-arm/baseline-lock.json`;
- `experiments/20260831-four-arm/baseline-run-map.json`;
- `experiments/20260831-four-arm/v6-baseline-token-attribution.json`;
- all `o*-g2-result.json` files;
- all `v6-token-efficient-prompt-*-result.json` files;
- `g3-case-set.json`, labelled as historical result-aware selection rather than
  a valid new preregistered set;
- exact Method, psi-agent, evaluator, prompt, and input hashes.

### Ideas that may be reimplemented, not cherry-picked

- Unknown token fields must remain unknown rather than being treated as zero.
- Billing totals include all attempts, while the canonical answer is the first
  successful allowed attempt.
- Only predeclared infrastructure failures may be retried.
- Case IDs, ordering, input files, and rendered prompt bytes should be hashed
  and frozen before execution.

These principles must be implemented in domain-neutral experiment-control code
without TravelPlanner failure strings, evaluator-aware retry paths, or cache
collection duplicated from psi-agent.

## 6. `src/travelplanner_experiment/` file-by-file audit

The union below covers files present across the old feature stack, four-arm
branch, v6 branch, and PR #13-#16 stack.

### `__init__.py`

Current role: package exports for `Case` and `render_prompt`.

Disposition: **keep only after narrowing exports to the new neutral harness**.

Allowed content is package wiring with no solver behavior. Do not export typed
tools, validators, repair helpers, runtime patches, or treatment variants.

### `protocol.py`

Current role: combines the frozen TravelPlanner task/output contract with
`WORKFLOW_V1`, `WORKFLOW_V2`, `WORKFLOW_V3`, CC Dynamic, v5, v6, and later
benchmark-local treatment prompts.

Disposition: **rewrite; do not keep the current file**.

Keep:

- `Case` or an equivalent immutable case identity;
- the frozen common TravelPlanner user task/output contract, identical for all
  arms;
- byte-stable rendering and literal query preservation;
- only the minimal preregistered activation difference, currently represented
  by `WORKFLOW_V1 = "Please complete the task using workflow skill.\n\n"`.

Remove:

- `WORKFLOW_V2` and `WORKFLOW_V3`;
- `CC_DYNAMIC_WORKFLOW_PROMPT_TEMPLATE` as a Workflow treatment;
- all `V5_*` and `V6_*` contracts;
- authoring syntax instructions;
- candidate collection/selection rules;
- validator, repair, fallback, routing, and single-consumer rules;
- exact TravelPlanner failure-derived rules such as route completion,
  multi-city viability, field repair, and empty-plan fallback.

Important: the benchmark's official task/output contract is necessarily
TravelPlanner-specific and is allowed only because it is frozen and identical
across comparison arms. It must not contain arm-specific Workflow advice.

### `tools.py`

Current role: per-case, read-only adapter over official TravelPlanner reference
rows, exposing flights, accommodations, restaurants, attractions, and distance.

Disposition: **conditionally keep as frozen benchmark infrastructure**.

Conditions:

- expose the same data and schemas to every comparison arm;
- do not pre-filter, compact, rank, normalize away source fields, or inject
  evaluator knowledge;
- do not change availability based on whether Workflow is activated;
- do not use tool responses to trigger model retries or repair;
- document and hash the exact adapter version before a run.

Review `_strip_parenthetical`, `_normalize`, and generated no-result strings
against the official tool/data contract. If they differ from the official
baseline surface, replace the adapter with the same official tool layer for all
arms rather than treating this file as authoritative.

### `workflow_io.py`

Current role: workspace-confined read/write helper; later versions add special
read-once behavior for Workflow Skill and grammar paths.

Disposition: **keep only generic workspace confinement; remove special cases**.

Keep:

- path resolution constrained to the isolated per-case workspace;
- ordinary file read/write behavior required to author a Workflow.

Remove:

- `read_once_references`;
- `_reference_key` aliases for Skill/G4 files;
- forced atomic full-file reads;
- `[Already loaded]` behavior;
- TravelPlanner-attempt-specific messages.

If production psi-agent already provides the same workspace file boundary, use
that production implementation instead of maintaining a benchmark-local twin.

### `skill_overlay.py`

Current role: injects `workflow_skill_guidance.md` into an isolated Workflow
Skill copy.

Disposition: **remove entirely from the Method repository**.

A benchmark-local overlay is a treatment-only Skill fork. Any admissible Skill
change must be edited and tested in psi-agent, then frozen as the production
method version used identically wherever Workflow is activated.

### `workflow_skill_guidance.md`

Current role: planning, Artifact, quality-gate, validation, and repair guidance.

Disposition: **remove from Method; do not copy verbatim to psi-agent**.

Why it cannot move verbatim:

- it makes planning explicit in the authoring context, encouraging the verbose
  explanation/candidate behavior that needs to be reduced;
- it explicitly lists candidate membership, budget, route/date, and constrained
  planning flow shapes;
- it prescribes validation/repair based on TravelPlanner-observed failures;
- it was introduced and evaluated inside the TravelPlanner experiment.

Potential general hypothesis for a new psi-agent change:

> The author should internally resolve dependencies and select one executable
> graph, then emit only the final G4 source and the minimal execution notice,
> without exposing candidate graphs, revisions, or explanatory drafts.

The new text must use unrelated examples such as code review, ETL, or document
processing, and must not mandate a validator or repair step for every task.

### `typed_tools.py`

Current role: converts official tables into compact JSON and applies lodging,
occupancy, room-type, house-rule, route, and tool-visibility policies.

Disposition: **remove entirely**.

It changes the candidate set, schemas, context length, selection difficulty,
tool availability, and therefore quality/token/latency. It encodes
TravelPlanner constraint logic and is not neutral plumbing.

Do not preserve a "formatting-only" subset without a preregistered all-arm tool
contract; structured conversion itself can materially change model behavior.

### `validator.py`

Current role: validates TravelPlanner membership, repeated restaurants,
accommodation nights/occupancy, traveler count, budget, and other plan rules;
its result drives repair and fallback.

Disposition: **remove entirely from the model-visible or execution path**.

The official evaluator may run after output is finalized, hidden from the
model. Evaluator/validator output must never trigger retries, prompt changes,
repair, or acceptance decisions.

### `token_accounting.py`

Current role: parses historical psi-agent logs and Workflow sidecars, reconciles
outer and inner usage, handles cache fields, and selects canonical reruns.

Disposition: **remove from the new Method code; archive with historical
analysis if needed**.

Reasons:

- cache/token transport is already implemented in the psi-agent version used
  for the prior 30-case run;
- the parser is coupled to historical log messages, paths, and sidecar shapes;
- reintroducing it as a treatment would double-count or create arm-specific
  overhead.

For the new experiment, freeze one psi-agent version for all arms and collect
usage through one identical external harness/sidecar path. Token/cache
accounting is measurement infrastructure, not a Workflow treatment.

### `experiment_control.py`

Current role: provider-neutral usage structures, failure classification, retry
eligibility, canonical attempt selection, and billed usage aggregation.

Disposition: **rewrite as neutral harness code; do not cherry-pick current
implementation**.

Keep the abstract policies listed in section 5. Remove:

- `validate_travel_plan` and second-validation markers;
- `VALIDATOR`, `EVALUATOR_QUALITY`, or Workflow-planning categories if they are
  used to alter retry behavior after inspecting task results;
- benchmark-specific error-string heuristics;
- any distinction that lets one arm resample a model-generated failure.

Pre-register a small, provider-level retry taxonomy based only on transport and
process evidence. Model output, parseability, Workflow authoring failure,
timeout after billable model usage, validator failure, and evaluator quality
must be final unless the same fixed policy is explicitly preregistered for all
arms.

### `case_selection.py`

Current role: validates TravelPlanner manifest metadata, aligns prompt rows,
parses selected IDs, writes ordered JSONL, and hashes bytes.

Disposition: **split and rewrite**.

Keep in neutral form:

- explicit preregistered case IDs;
- duplicate/missing-ID rejection;
- identical ordering across arms;
- deterministic serialization and SHA-256.

Do not keep:

- TravelPlanner-specific `REQUIRED_METADATA` in generic experiment control;
- selection based on known failed cases, token outliers, or prior traces;
- separate prompt sources chosen according to prior result availability.

TravelPlanner schema validation may remain as a frozen dataset-loader concern,
but it must not choose cases or alter prompts by arm.

### `runtime.py`

Current role: PR #14/#16-era benchmark-local registration of a psi-agent
runtime patch/revision.

Disposition: **remove entirely**.

Runtime capabilities must be present directly in the one frozen psi-agent
commit used for every applicable arm. Method must record the commit/hash, not
apply or select runtime patches per treatment.

## 7. General method candidates for psi-agent

Only the following two candidates were approved for further design. They are
not yet implemented in the clean worktree.

### A. Quiet, decisive authoring

Domain-independent hypothesis:

> A Workflow author can perform intent and dependency analysis internally,
> select one executable graph, and author it without emitting explanations,
> modification history, candidate graphs, or alternative solutions. This
> reduces authoring tokens and ambiguity without reducing the graph's task
> coverage.

Method owner: production Workflow Skill in psi-agent.

Required properties:

- no TravelPlanner vocabulary or examples;
- no blanket instruction to add budget/route/membership quality gates;
- no fixed TravelPlanner graph shape;
- do not suppress necessary user clarification when the task is genuinely
  ambiguous;
- keep the final G4 source and minimal execution notice;
- add non-TravelPlanner tests/fixtures, for example code-review fan-out/fan-in
  and an ETL pipeline;
- measure authoring validity and token/latency separately from TravelPlanner
  score.

### B. G4/operator parameter documentation

Domain-independent hypothesis:

> Making operator owner, parameter types, return type, arity, and legal
> assertion shape explicit in the authoritative G4/catalog documentation
> improves first-attempt source validity across domains without changing parser
> or runtime semantics.

Method owner: production Workflow grammar/catalog documentation in psi-agent.

The current grammar already documents signatures such as:

```text
agent_config(Agent, Model, Engine, ApiBase) -> Bool [arity 4]
allowed_tool(Agent, Tool) -> Bool [arity 2]
```

Any additional guidance should explain generic legal forms, for example that a
Bool-returning operator may be a standalone assertion and that each scalar tool
grant is a separate call. Do not mention `search_flights` or prohibit
`agent_config` for one benchmark. Ordinary G4 comments are model-visible
documentation but parser/runtime-invisible; they still affect authoring quality,
tokens, and latency and therefore must be treated as an experimental method
variable, not as a no-effect cleanup.

Do not conflate ordinary G4 comments with `@artifact` directives. In the
historical runtime, `@artifact` comments are re-parsed and affect schemas,
prompts, validation, Program output parsing, and failure paths.

## 8. Proposed new canonical stacks

### Method-on-TravelPlanner

Create new branches from `origin/main`, not from PR #2, #10, #11, #12, or the
historical v6 branch:

```text
origin/main
+-- experiment/neutral-travelplanner-harness
    +-- experiment/preregistered-workflow-arm
```

The neutral harness should contain only:

- frozen case loading and schema validation;
- one common task/output contract for all arms;
- the same official data tools and data visibility for all arms;
- isolated workspaces/sessions;
- raw output, timing, usage, commit, configuration, and input provenance;
- hidden post-hoc official evaluation;
- the minimal preregistered Workflow activation difference in the Workflow arm.

Do not add v2/v3/v4/v5/v6 variants to this line.

### psi-agent

Create a small stacked series from the selected production baseline or another
explicitly agreed production commit:

```text
production baseline
+-- method/workflow-quiet-authoring
    +-- method/workflow-operator-guidance
```

Keep these changes separate because both are model-visible performance
variables. Each PR must state its domain-independent hypothesis, include a
non-TravelPlanner example/test, and be independently measurable.

Do not include cache accounting as another treatment. All experiment arms must
use the same accounting-enabled or accounting-disabled psi-agent version.

## 9. Experiment design constraints

Before running any model call, freeze and hash:

- Method commit;
- psi-agent commit;
- Workflow Skill and G4/catalog files;
- model/provider/base URL identifier without secrets;
- model parameters, reasoning effort, context limits, and retry policy;
- case IDs and ordering;
- task/output prompt bytes;
- tool names, schemas, implementation hashes, and visibility;
- dataset/reference inputs;
- official evaluator commit and relevant file hashes;
- timeouts and concurrency;
- result directory schema.

All comparison arms must use the same model, inputs, tools, retry policy,
evaluator, and accounting path. The only difference should be the single
preregistered method variable.

Do not run a benchmark merely to decide how to amend a prompt. A failed
preregistered treatment is a result, not an instruction to patch and rerun the
same evaluation cases.

## 10. Working-tree safety and current state

Do not clean or reset the main psi-agent worktree. It contains user changes:

```text
/public/home/sychen/cxy/workflow/psi-agent
branch: feat/resume-approval-lite-workflow
modified:
  examples/haitun-workspace/skills/workflow/SKILL.md
  examples/haitun-workspace/skills/workflow/fusion_flow/workflow_runner.py
  src/psi_agent/_run.py
```

Historical worktrees inspected during this audit were clean:

```text
/public/home/sychen/cxy/workflow/method-wt-v6-clean
/public/home/sychen/cxy/workflow/method-travelplanner-wt-four-arm-v1
/public/home/sychen/cxy/workflow/psi-agent-wt-v6-protocol-standalone
```

A clean psi-agent worktree was created for the proposed method work but no
source changes or commits were made:

```text
/public/home/sychen/cxy/workflow/psi-agent-wt-general-quiet-authoring
branch: experiment/general-quiet-authoring
HEAD: a9579c7d4f544be24efd59dcb6ef0c3a07e48863
status: clean
```

The next process may reuse that worktree after confirming the desired branch
name and baseline. It should not assume that merely creating the worktree
authorizes implementation or benchmark execution.

## 11. Recommended execution order for the next process

1. Read the workspace `AGENTS.md` and this handoff completely.
2. Fetch remote state and re-check PR heads; do not mutate old branches.
3. Preserve/tag historical #1, #10, #11, #12, and v6 provenance before any PR
   closure or branch cleanup.
4. Create a new Method branch from `origin/main` and reconstruct the neutral
   harness; do not cherry-pick PR #2 wholesale.
5. Prove by diff that the new Method line contains no v2-v6 prompt, typed tool,
   validator, repair, Skill overlay, runtime patch, or cache implementation.
6. Independently implement quiet authoring in psi-agent with non-TravelPlanner
   tests.
7. Independently implement/adjust G4 operator guidance in psi-agent with
   non-TravelPlanner syntax cases.
8. Run unit tests, lint, and `git diff --check`; scan method diffs for
   TravelPlanner/domain vocabulary.
9. Open replacement PRs and mark old PRs superseded. Do not merge without
   explicit user authorization.
10. Draft a preregistration manifest and obtain user approval before any new
    model or benchmark run.

## 12. Non-goals

The cleanup must not:

- reproduce the previous v6 score through hidden benchmark logic;
- optimize specifically for known failed case IDs;
- treat lower token count as proof of unchanged quality;
- claim prompt/comment changes have no performance effect;
- apply validator feedback during generation;
- hide treatment differences in a benchmark-local tool adapter;
- rewrite the provenance of the prior 30-case run;
- merge or delete branches solely to make the graph look linear.
