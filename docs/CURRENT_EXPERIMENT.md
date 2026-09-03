# Current Experiment Contract

## Method Boundary

The experiment harness freezes case identity, prompt bytes, task data access,
model configuration, retry policy, and evaluator procedure. Its only treatment
activation is the preregistered prefix stored in `experiment/runner.py`.
Benchmark-local code does not validate, repair, rank, or accept model answers.

General capabilities are owned by psi-agent's Workflow Skill, runtime,
Artifact transport, scheduler, grammar, or protocol. They are developed only
in sibling worktrees and reach the baseline only through an upstream PR.

## Frozen Inputs

- Cases, in order: `1, 11, 14, 17, 28, 33, 38, 41, 46, 48, 70, 72, 77, 81,
  83, 100, 110, 113, 116, 118, 123, 124, 138, 144, 146, 151, 159, 161, 162,
  163`.
- Manifest SHA-256:
  `a55b1ba56722c4fae7f020b88a95bc18b171a278088163c4db22b2f804690045`.
- Prompt-query SHA-256:
  `e026647b205dedce0d9ebb2f2a659c2e710ba9288b51704037b2d2cb7c61a9b4`.
- Prompt-template SHA-256:
  `08216d1b8ac0ddac402f11c8d9d3c9333e69a5345c9f92f706029ec8b4aac346`.
- Treatment prefix: `Please complete the task using workflow skill.` followed
  by two newlines.

## Current Baseline

- Repository: `https://github.com/1DivSin/psi-agent.git`.
- Commit: `6d22e72b31c28c1fb935f89bf21894c5853de059`.
- PR #21: domain-neutral adversarial verifier authoring guidance.
- PR #22: programmatic structured Artifact schema execution.
- PR #24: reverts PR #23's bounded authoring defaults.

The baseline source must be clean. The harness hashes the copied Workflow
Skill, grammar, runtime, task adapters, frozen inputs, and itself in every new
run's provenance.

## Execution And Evaluation

Default concurrency is 10. The default maximum of three attempts applies only
to declared process or transport failures. Prompts never change between
attempts. Parsed output is recorded without a quality decision.

The official evaluator is absent from the inference workspace and runs only
after inference completes. No evaluator verdict, case trace, or observed
failure may choose a retry, prompt amendment, graph amendment, filtering rule,
or acceptance path.

## Historical Archive

The archived 30-case run used psi-agent `6d97204b...`; it is retained as raw
evidence and is not a run of the current baseline. The evaluator archive is
marked `INTERIM_DIAGNOSTIC_NOT_FORMAL_BENCHMARK_RESULT`. See
`HISTORICAL_METHOD_AUDIT.md` for rejected benchmark-specific approaches that
must not be migrated.
