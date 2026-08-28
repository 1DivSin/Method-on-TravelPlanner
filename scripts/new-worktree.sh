#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 <branch> [base]" >&2
  echo "example: $0 feature/typed-candidates origin/main" >&2
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
  exit 2
fi

branch=$1
base=${2:-origin/main}

if [[ ! $branch =~ ^(feature|fix|docs|chore)/[a-z0-9][a-z0-9._-]*$ ]]; then
  echo "error: branch must match feature|fix|docs|chore/<lowercase-slug>" >&2
  exit 2
fi

repo_root=$(git rev-parse --show-toplevel)
repo_name=$(basename "$repo_root")
worktree_root=$(dirname "$repo_root")/.worktrees
slug=${branch//\//-}
target=$worktree_root/$repo_name-$slug

git fetch origin

if git show-ref --verify --quiet "refs/heads/$branch"; then
  echo "error: local branch already exists: $branch" >&2
  exit 1
fi
if [[ -e $target ]]; then
  echo "error: worktree target already exists: $target" >&2
  exit 1
fi

mkdir -p "$worktree_root"
git worktree add -b "$branch" "$target" "$base"

echo "$target"
