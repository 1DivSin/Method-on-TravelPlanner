# TravelPlanner Experiment Rules

These rules apply to this directory and all descendants. They add to, and do
not weaken, the workspace-wide `AGENTS.md`.

## Scope

This directory is experiment control and read-only result history. It is not a
home for benchmark solver logic. Benchmark-local code is limited to:

- loading preregistered cases and frozen prompts;
- exposing the same frozen task data and tools to every comparison arm;
- isolating workspaces and processes;
- recording configuration, provenance, raw responses, and process failures;
- preparing evaluator input after inference is complete.

The evaluator must remain hidden from the model and must never drive retries,
repair, prompt changes, graph changes, filtering, or result acceptance.

## No Ad Hoc Work

Do not add benchmark-specific solver prompts, heuristics, graph shapes,
validators, quality gates, repair policies, candidate filters, fallback rules,
tool-call strategies, or privileged data paths. Do not derive a method change
from case outputs, traces, failures, or evaluator feedback.

Except for one preregistered method variable, comparison arms must keep the
same model, sampling settings, retry policy, cases, prompt bytes, task tools,
data access, and evaluator procedure. Retries may cover only predeclared
process or transport failures and must reuse the byte-identical prompt.

Before any method change, write a domain-independent hypothesis and identify
its owner in the Workflow Skill, runtime, Artifact transport, scheduler,
grammar, or protocol. The change must include domain-neutral tests and at least
one non-TravelPlanner example.

Mandatory counterfactual:

> If TravelPlanner and all of its vocabulary were removed, would this exact
> change still improve Workflow when Haitun is used for a different task?

If the answer is no, uncertain, or depends on benchmark behavior, stop. Do not
implement, commit, push, or include the change in an experiment.

## Worktrees Only

`psi-agent/` is a detached, clean baseline. Never develop or commit in it.
Every method change must start from the latest upstream `main` in a separate
worktree under `worktrees/`, with one branch and one feature per worktree.

From this directory:

```bash
git -C psi-agent fetch git@github.com:1DivSin/psi-agent.git main
git -C psi-agent worktree add -b method/<slug> ../worktrees/<slug> FETCH_HEAD
```

Do not copy an old worktree: Git worktree metadata is path-bound. Do not place
virtual environments, run outputs, evaluator assets, or benchmark data in a
psi-agent feature branch.

## Pull Requests

General method features must be committed in their dedicated worktree, pushed
to `1DivSin/psi-agent`, and submitted as a PR. Never push directly to `main`.
For a branch named `method/<slug>`:

```bash
git -C worktrees/<slug> push git@github.com:1DivSin/psi-agent.git \
  HEAD:refs/heads/method/<slug>
gh pr create --repo 1DivSin/psi-agent --base main --head method/<slug>
```

The PR description must include:

- the domain-independent method hypothesis and method-level owner;
- the production files changed and why they are generic;
- domain-neutral tests, including a non-TravelPlanner example;
- confirmation that benchmark inputs, tools, and evaluator were not added;
- the mandatory counterfactual audit above.

Experiment-only files stay here and must not be uploaded to psi-agent.
