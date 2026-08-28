# Repository workflow

All implementation, documentation, experiment-result, and configuration changes
must be delivered through pull requests.

## Required process

1. Never commit directly to `main` and never edit a branch that belongs to an
   unrelated open PR.
2. Fetch the remote state before starting a change.
3. Create one dedicated Git worktree and one branch for each independently
   reviewable change. Use `feature/<slug>`, `fix/<slug>`, `docs/<slug>`, or
   `chore/<slug>`.
4. Keep each PR focused. Split independent behavior changes; use stacked PRs
   when a later change genuinely depends on an earlier one.
5. Add or update tests in proportion to the behavior changed. Run the relevant
   test suite and `git diff --check` before committing.
6. Commit, push the branch, and create a non-draft PR. The PR body must state
   the behavior, verification, and any base-branch dependency.
7. Do not merge a PR unless the user explicitly requests merging.
8. Preserve unrelated worktree changes and never use destructive reset or
   checkout commands to clean another contributor's work.

For a normal independent change, start with:

```bash
scripts/new-worktree.sh feature/my-change
```

For a dependent stacked change, pass the preceding remote branch as the second
argument:

```bash
scripts/new-worktree.sh feature/next-change origin/feature/previous-change
```
