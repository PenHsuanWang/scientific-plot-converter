# Contributing to FabPlot-CLI

This document describes the Git workflow, branch strategy, pre-commit quality
gates, and CI/CD pipeline used by this project.

> 📖 **For the full developer SOP** (implementation order, typography constants,
> architecture decisions, release recovery steps) see **[HANDBOOK.md](HANDBOOK.md)**.

---

## Table of Contents

1. [Git Flow Overview](#1-git-flow-overview)
2. [Branch Naming](#2-branch-naming)
3. [Commit Message Convention](#3-commit-message-convention)
4. [Local Development Setup](#4-local-development-setup)
5. [Pre-Commit Quality Gates](#5-pre-commit-quality-gates)
6. [Feature Development Lifecycle](#6-feature-development-lifecycle)
7. [CI Pipeline — Push & Pull Request](#7-ci-pipeline--push--pull-request)
8. [Release Pipeline — Version Tagging](#8-release-pipeline--version-tagging)
9. [Hotfix Flow](#9-hotfix-flow)

---

## 1. Git Flow Overview

This project uses a **two-protected-branch** model:

```
                         ┌──────────────────────────────────────┐
                         │              GitHub                    │
                         │                                        │
  ┌──────────────────────┤  master  (protected, merge-only)      │
  │                      └────────────────┬───────────────────────┘
  │                                       │ PR merge (dev → master)
  │  ┌────────────────────────────────────┤
  │  │  dev  (protected, integration)     │
  │  └────────────────┬───────────────────┘
  │                   │ PR merge (feature → dev)
  │  feature/<N>-<slug>
  │
  │  Each feature lives on its own branch and merges to dev first.
  │  No direct pushes to master or dev — changes arrive only via Pull Request.
  │  All CI checks must be green before merge is allowed.
  │
  │  Releases:  bump version on dev  →  PR dev → master  →  push tag
  │
  └──  master  ──► git push origin vX.Y.Z  ──► release.yml  ──► GitHub Release
```

### Golden Rules

- **Never push directly to `master` or `dev`.**  All changes enter via Pull Request.
- **Features go to `dev` first.**  Only `dev → master` PRs cut a release.
- **One logical change per PR.**  Keep diffs reviewable.
- **Pre-commit hooks are mandatory.**  They run locally before every commit and
  identically in CI — a hook failure locally means a CI failure remotely.
- **Tests must pass before review.**  Run `tox` locally before opening a PR.

---

## 2. Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/<issue-number>-<short-description>` | `feature/1-standard-plot-format` |
| Bug fix | `fix/<issue-number>-<short-description>` | `fix/14-histogram-bin-edge-error` |
| Documentation | `docs/<issue-number>-<short-description>` | `docs/22-update-api-reference` |
| Hotfix (critical) | `hotfix/<issue-number>-<short-description>` | `hotfix/31-cpk-division-by-zero` |
| Version bump | `chore/bump-vX.Y.Z` | `chore/bump-v0.2.0` |

Rules:
- Use lowercase and hyphens only (no underscores, no slashes except the prefix).
- The issue number comes first so branches sort predictably.
- Keep `<short-description>` to 3–5 words maximum.

---

## 3. Commit Message Convention

```
<type>(<scope>): <imperative summary, ≤72 chars>

[optional body — explain *why*, not *what*]

[optional footer — e.g. Closes #14]

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

### Types

| Type | When to use |
|------|-------------|
| `feat` | New feature or subcommand |
| `fix` | Bug fix |
| `refactor` | Code restructuring without behaviour change |
| `perf` | Performance improvement |
| `docs` | README, Sphinx, or docstring-only changes |
| `test` | Test additions or corrections |
| `chore` | Tooling, CI config, dependency bumps |
| `style` | Formatting fixes (auto-applied by ruff — rarely needed manually) |

### Examples

```
feat(cli): add compare subcommand with 7:3 composite layout

fix(engine): prevent tick label overlap on narrow canvases

docs: document three-tier typography flags in README

test(metrics): add edge-case tests for calculate_ratio with zeros
```

---

## 4. Local Development Setup

```bash
# 1. Clone and enter the repository
git clone https://github.com/PenHsuanWang/scientific-plot-converter
cd scientific-plot-converter

# 2. Create and activate an isolated virtual environment (uv recommended)
uv venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows

# 3. Install the package and all dev dependencies in editable mode
uv pip install -e ".[dev]"

# 4. Register pre-commit hooks (one-time per clone)
pre-commit install
```

> **Important — mypy hook:**
> The `mypy` pre-commit hook is configured with `language: system`, meaning it
> resolves imports from whichever Python is active in your shell.  **Always
> activate `.venv` before running `git commit`**, otherwise the hook fails with
> *"Executable `mypy` not found."*

---

## 5. Pre-Commit Quality Gates

The following hooks run automatically on every `git commit`.  They also run
verbatim in the `pre-commit` CI job.

| Hook | Source | What it checks / fixes |
|------|--------|------------------------|
| `trailing-whitespace` | pre-commit/pre-commit-hooks v4.5.0 | Removes trailing spaces |
| `end-of-file-fixer` | pre-commit/pre-commit-hooks v4.5.0 | Ensures single trailing newline |
| `check-yaml` | pre-commit/pre-commit-hooks v4.5.0 | Validates YAML syntax |
| `check-added-large-files` | pre-commit/pre-commit-hooks v4.5.0 | Blocks files > 500 KB |
| `ruff --fix` | astral-sh/ruff-pre-commit v0.2.2 | PEP 8 lint + import ordering; auto-fixes safe issues |
| `flake8` | local (flake8 ≥ 7.0 + flake8-docstrings ≥ 1.7) | PEP 8 style + PEP 287 reST docstrings on `src/` and `tests/` |
| `mypy src/` | local (`language: system`) | Strict static type checking across the entire package |

### Running Hooks Without Committing

```bash
# Dry-run all hooks across every tracked file
pre-commit run --all-files

# Run a single hook by ID
pre-commit run flake8 --all-files
pre-commit run mypy --all-files
```

### Common Hook Failures and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `E501 line too long` | Line > 88 chars | Wrap with `\` or parentheses |
| `D107 Missing docstring in __init__` | No docstring on `__init__` | Add `"""..."""` (even one line) |
| `D403 First word should be capitalized` | Lowercase start | Capitalize first word |
| `mypy: Executable not found` | `.venv` not active | Run `source .venv/bin/activate` first |
| `mypy: error: ...` | Type annotation mismatch | Fix return type or add explicit annotation |

---

## 6. Feature Development Lifecycle

```
 GitHub Issue created
         │
         ▼
 git checkout -b feature/<N>-<slug>
         │
         ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │  LOCAL DEVELOPMENT LOOP                                                   │
 │                                                                           │
 │  1. Update SRS.md + SDD.md  (requirements before code)                   │
 │  2. Edit source files in dependency order:                                │
 │        engine.py → metrics.py → plots.py → cli.py → test_cli.py          │
 │  3. pytest tests/ -q          (smoke check after each file)              │
 │  4. tox                       (full lint + test; mirrors CI)             │
 │  5. sphinx-build -b html docs docs/_build/html -q  (verify 0 warnings)   │
 └───────────────────────────────────────────────────────────────────────────┘
         │
         ▼
 git add <files>
 git commit -m "feat: ..."
         │
         ▼  (pre-commit hooks fire automatically)
         │
         │  ✖ Hooks fail → fix → git add -u → git commit
         │  ✔ Hooks pass → commit recorded
         │
         ▼
 git push origin feature/<N>-<slug>
         │
         ▼
 Open Pull Request → dev
         │
         ▼  (CI pipeline triggers — see §7)
         │
         │  ✖ CI fails → push fixes to same branch → CI re-runs
         │  ✔ CI passes → request review
         │
         ▼
 PR reviewed and approved
         │
         ▼
 Merge into dev
         │
         ▼
 Delete feature branch
```

---

## 7. CI Pipeline — Push & Pull Request

**Trigger:** every `push` and `pull_request` targeting `dev` or `master`.

```
push / pull_request → dev or master
        │
        ├─── Workflow: CI (ci.yml)
        │         ├── Job: pre-commit  ──────────────────────────────────────────┐
        │         │         runs-on: ubuntu-latest                               │
        │         │         python: 3.13                                         │
        │         │         steps:                                               │
        │         │           pip install -e ".[dev]"   ← needed by mypy hook   │
        │         │           pip install pre-commit                             │
        │         │           pre-commit run --all-files                         │
        │         │                                                              │
        │         └── Job: tox  (matrix: lint | test)  ──────────────────────── ┘
        │                   runs-on: ubuntu-latest
        │                   python: 3.13
        │                   strategy.matrix.tox-env: [lint, test]
        │                   steps:
        │                     pip install tox
        │                     tox -e ${{ matrix.tox-env }}
        │
        └─── Workflow: Docs (docs.yml)
                  ├── Job: build   sphinx-build (all PR/push triggers)
                  └── Job: deploy  gh-pages push (master push only)
```

### What Each Tox Environment Runs

**`tox -e lint`**

```bash
ruff check src tests          # fast import-order + style lint
flake8 src tests              # PEP 8 + PEP 287 docstring enforcement
mypy src                      # strict static type checking
```

**`tox -e test`**

```bash
pytest tests/ --cov=fabplot --cov-report=term-missing
```

### Pass / Fail Semantics

| Scenario | Result |
|----------|--------|
| All jobs green | PR may be merged |
| Any job red | PR is blocked; push a fix commit to the same branch |
| Flaky test (passes on retry) | Investigate root cause; do not merge flaky code |

### Viewing CI Results

1. Open the PR on GitHub.
2. Scroll to the **Checks** section at the bottom.
3. Click a job name to expand step-level logs.
4. For failed steps, click the step to see the exact error output.

---

## 8. Release Pipeline — Version Tagging

**Trigger:** a `push` of a tag matching `v[0-9]+.[0-9]+.[0-9]+` (e.g. `v0.2.0`).

### ⚠️ `master` is Protected — Follow This Order Exactly

```
WRONG ❌  git checkout master → bump → git push --follow-tags
          → rejected: "Changes must be made through a pull request"

CORRECT ✅  Bump on dev → PR dev→master → merge → push tag only
```

### Semantic Version Rules

| Change type | Bump | Before → After |
|-------------|------|----------------|
| Bug fix only | `patch` | `0.1.0 → 0.1.1` |
| New feature, backward-compatible | `minor` | `0.1.0 → 0.2.0` |
| Breaking API / CLI change | `major` | `0.1.0 → 1.0.0` |

### Step-by-Step Release Procedure

```bash
# 1. Start from a clean dev branch
git checkout dev && git pull

# 2. Activate the virtual environment (bump-my-version is in .venv)
source .venv/bin/activate

# 3. Preview the bump (nothing is written)
bump-my-version bump minor --dry-run --verbose

# 4. Apply the bump ON DEV
bump-my-version bump minor
#   Automatically:
#     • Updates version = "..." in pyproject.toml
#     • Updates __version__ = "..." in src/fabplot/__init__.py
#     • Creates commit "Bump version: 0.1.0 → 0.2.0"
#     • Creates LOCAL annotated tag v0.2.0

# 5. Push the bump commit to dev
git push origin dev

# 6. Open Pull Request: dev → master on GitHub
#    Wait for CI to pass, then merge.

# 7. After merge, pull master locally
git checkout master && git pull

# 8. Push the tag (this triggers release.yml)
git push origin v0.2.0
#    ↑ Push the tag name directly — do NOT use --follow-tags here
#    (that would try to push to master too, which is blocked)
```

> **Never edit version strings manually.**  Only `bump-my-version` keeps
> `pyproject.toml` and `src/fabplot/__init__.py` in sync and creates the
> required annotated tag.

### Recovery: Accidentally Bumped on `master`

```bash
git checkout master
git reset --hard origin/master   # discard local bump commit
git tag -d vX.Y.Z                # delete local tag
git checkout dev
bump-my-version bump minor       # redo on dev
git push origin dev              # then follow steps 6-8 above
```

### What Happens on GitHub After Tag Push

```
git push origin v0.2.0
        │
        ├─── Job: ci  (lint + test guard) ────────────────────────────────────┐
        │         tox -e lint                                                   │
        │         tox -e test                                                   │
        │         must pass before downstream jobs run                         │
        │                                                                       │
        ├─── Job: build  (needs: ci) ──────────────────────────────────────────┤
        │         python -m build                                               │
        │         produces dist/fabplot_cli-0.2.0.tar.gz                       │
        │                  dist/fabplot_cli-0.2.0-py3-none-any.whl             │
        │         uploads both as GitHub Actions artifact "dist"               │
        │                                                                       │
        └─── Job: release  (needs: build) ────────────────────────────────────┘
                  downloads artifact "dist"
                  gh release create v0.2.0 dist/*
                    --title "Release v0.2.0"
                    --generate-notes          ← auto-builds changelog from commits
```

The published release is visible at **GitHub → Releases**.  Both the source
distribution (`.tar.gz`) and the wheel (`.whl`) are attached as downloadable
assets.

---

## 9. Hotfix Flow

A hotfix addresses a critical defect in the production release **without**
waiting for in-progress feature branches.

```
master (currently at v0.2.0)
  │
  └── git checkout -b hotfix/31-cpk-division-by-zero
            │
            ▼
        minimal fix + test
            │
            ▼
        tox (lint + test must pass)
            │
            ▼
        git commit -m "fix: guard Cpk against zero-sigma denominator"
            │
            ▼
        git push origin hotfix/31-cpk-division-by-zero
            │
            ▼
        Open PR → master  (hotfixes skip dev and go straight to master)
            │  CI passes
            ▼
        Merge → master
            │
            ▼
        git checkout dev && git pull master  ← backport to dev
            │
            ▼
        git checkout dev
        bump-my-version bump patch  →  v0.2.1   (on dev)
        git push origin dev
        Open PR: dev → master (or push tag directly if repo admin)
        git push origin v0.2.1    →  release pipeline
```

Hotfix branches are deleted after the PR merges, just like feature branches.

---

*This document is owned by the FabPlot-CLI maintainers and should be updated
whenever the CI configuration or branching conventions change.*
