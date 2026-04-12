# dsprinter — Developer Handbook

> **Scope:** This handbook records the proven development SOP for `dsprinter`.
> It covers git flow, feature development order, testing protocol, documentation
> build, and version/release tagging. Follow these steps for every new feature.

---

## 1. Repository Bootstrap (One-Time)

```bash
git clone https://github.com/PenHsuanWang/scientific-plot-converter
cd scientific-plot-converter
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
pre-commit install          # register git hooks into .git/hooks/pre-commit
```

> **Note:** `pre-commit install` must be run once per clone. The `mypy` hook uses
> `language: system` — the `.venv` **must be active** every time you `git commit`.

---

## 2. Git Branch Strategy

This project uses a **two-protected-branch gitflow**:

```
master  ←── production; protected; tag-triggered releases; merged via PR only
  │
dev     ←── integration; protected; all features/fixes merge here first
  │
  └── feature/<issue-number>-<short-description>   (e.g. feature/1-standard-plot-format)
  └── fix/<issue-number>-<short-description>
  └── chore/<short-description>   (e.g. chore/bump-v0.2.0)
  └── docs/<issue-number>-<short-description>
```

> ⚠️ **Never push directly to `dev` or `master`** — both branches have GitHub branch
> protection rules requiring all changes to go through a Pull Request.

### Lifecycle

```
1. git checkout dev && git pull
2. git checkout -b feature/<N>-<description>
   ↓ develop (see §3 SOP below)
3. git add <files>
4. git commit -m "feat: <description>"   ← pre-commit hooks fire
5. git push origin feature/<N>-<description>
6. Open Pull Request: feature/<N>-<description> → dev
   ↓ GitHub Actions CI must pass (pre-commit + lint + test)
7. Merge PR to dev
8. When dev is stable: Open Pull Request: dev → master
   ↓ CI must pass again
9. Merge PR to master (triggers Sphinx doc deploy to gh-pages)
```

### Commit Message Convention

| Prefix | When to use |
|--------|-------------|
| `feat:` | New feature or command |
| `fix:` | Bug fix |
| `refactor:` | Code restructuring without behavior change |
| `docs:` | README, Sphinx, or docstring-only changes |
| `test:` | Tests only |
| `chore:` | Tooling, CI config, dependency bumps |

---

## 3. Feature Development SOP

Every feature **must** follow this order. Do not skip or reorder steps.

### Step 1 — Requirements (SRS + SDD)

Invoke the `requirements-analysis` skill, or manually:

1. Update `DSPrinter_SRS.md`:
   - Add User Stories under the relevant EPIC (or create a new EPIC)
   - Write BDD acceptance criteria (Given / When / Then) for each story
   - Update NFRs if the feature has performance or style constraints

2. Update `DSPrinter_SDD.md`:
   - Map new entities/value objects into the DDD model
   - Add new components/classes to the component table
   - Record design decisions (especially any alternatives considered)

### Step 2 — Implementation Order

Respect the dependency chain:

```
engine.py  →  metrics.py  →  plots.py  →  cli.py  →  test_cli.py
```

| File | What changes |
|------|-------------|
| `src/dsprinter/render/engine.py` | `DSPStyleContext` constants, `CanvasBuilder` helpers |
| `src/dsprinter/stats/metrics.py` | Pure computation functions (no I/O, no matplotlib) |
| `src/dsprinter/render/plots.py` | `render_*` functions using `CanvasBuilder` |
| `src/dsprinter/cli.py` | Typer command + options; calls render functions |
| `tests/test_cli.py` | New test classes covering all new paths |

### Step 3 — Testing Protocol

Run tests after every file you touch:

```bash
pytest tests/ -q                              # quick smoke check
pytest tests/ -q --cov=dsprinter --cov-report=term-missing   # with coverage
```

Rules:
- Every new public function needs at least one test.
- Every CLI command needs: happy-path test, missing-column test, bad-input test.
- `DSPStyleContext` must remain immutable — keep the `test_fab_style_context_is_frozen` test.
- Target: 0 failed tests, coverage ≥ 80% on new code.

### Step 4 — Linting & Type Checking

```bash
# Run the full quality gate (mirrors CI exactly)
tox

# Or individually:
tox -e lint    # ruff + flake8 + mypy
tox -e test    # pytest --cov=dsprinter
```

Common issues to fix before committing:

| Error code | Meaning | Fix |
|---|---|---|
| E501 | Line > 88 chars | Break with `\` or wrap in parens |
| D107 | Missing docstring in `__init__` | Add `"""..."""` even if one line |
| D403 | First word of docstring not capitalized | Capitalize |
| mypy `no return` | Missing return type annotation | Add `-> ReturnType:` |

### Step 5 — Documentation

**Docstrings** (required on all public functions and classes):

```python
def calculate_ratio(y1: np.ndarray, y2: np.ndarray) -> np.ndarray:
    """Compute element-wise ratio y2 / y1, NaN-safe.

    :param y1: Denominator array.
    :param y2: Numerator array.
    :returns: Array of ratios; NaN where y1 == 0.
    :rtype: numpy.ndarray
    """
```

**README.md** — update these sections when adding a feature:

1. `## Features` — add a bullet for new capability
2. `## Usage` — add a new `###` subsection with bash examples
3. `### Project Structure` — update file descriptions if new files added

**Sphinx** — verify the build is clean after any docstring changes:

```bash
sphinx-build -b html docs docs/_build/html -q
# Must exit 0 with no warnings
```

The `docs/api/` stubs use `automodule` — no manual edits needed there unless you
add an entirely new module (then add a new `.rst` stub and add it to `index.rst`).

### Step 6 — Pre-Commit & Final Verification

```bash
# Activate venv first (required by mypy system hook)
source .venv/bin/activate

# Run all hooks without committing (dry run)
pre-commit run --all-files

# If all green, commit
git add -u
git commit -m "feat: <description>"

# Hooks that fire on every commit:
#   trailing-whitespace, end-of-file-fixer, check-yaml,
#   check-added-large-files, ruff --fix, flake8, mypy
```

---

## 4. CI Pipeline Overview

```
push / pull_request to dev or master
         │
         ├─── Workflow: CI (ci.yml)
         │         ├── Job: pre-commit   → pre-commit run --all-files
         │         └── Job: tox (matrix, runs in parallel)
         │                   ├── tox -e lint   →  ruff + flake8 + mypy
         │                   └── tox -e test   →  pytest --cov=dsprinter
         │
         └─── Workflow: Docs (docs.yml)
                   ├── Job: build   → sphinx-build (runs on all PR/push triggers)
                   └── Job: deploy  → peaceiris/actions-gh-pages (master push only)
                                      → publishes to gh-pages branch
                                      → served at https://penhsuanwang.github.io/scientific-plot-converter/
```

All CI jobs (pre-commit, lint, test, docs build) must pass before a PR can be merged.

### Python Version Alignment

| Location | Version | Rule |
|---|---|---|
| `pyproject.toml` `requires-python` | `>=3.12` | Minimum supported |
| `pyproject.toml` `[tool.mypy]` `python_version` | `3.13` | Type-checking target |
| All `ci.yml` / `docs.yml` / `release.yml` | `3.13` | Must match local dev |
| `.pre-commit-config.yaml` | No `default_language_version` | Adapts to active env |

> ⚠️ **Do not add `default_language_version: python: X.Y`** to `.pre-commit-config.yaml`.
> Pre-commit should discover Python from the active venv. Hard-coding a version causes
> CI failures when the runner Python differs.

---

## 5. Version Tagging & Release SOP

### Semantic Versioning Rules

| Change type | Bump | Example |
|---|---|---|
| Bug fix only | `patch` | `0.1.0 → 0.1.1` |
| New feature, backward-compatible | `minor` | `0.1.0 → 0.2.0` |
| Breaking API change | `major` | `0.1.0 → 1.0.0` |

### ⚠️ Critical Rule: Bump on `dev`, Tag After `master` Merge

`master` is branch-protected — direct pushes are **rejected**. The version bump commit
must travel through a PR just like any other change.

```
WRONG ❌
  git checkout master
  bump-my-version bump minor
  git push --follow-tags   ← rejected by branch protection

CORRECT ✅
  Bump on dev → PR to master → merge → push tag only
```

### Full Release SOP

```bash
# ── Step 1: Ensure dev is clean and CI is green ────────────────────────────
git checkout dev && git pull

# ── Step 2: Bump version ON DEV (creates commit + local tag) ──────────────
source .venv/bin/activate
bump-my-version bump minor --dry-run --verbose   # preview first
bump-my-version bump minor
# → updates pyproject.toml  version = "0.2.0"
# → updates src/dsprinter/__init__.py  __version__ = "0.2.0"
# → creates commit: "Bump version: 0.1.0 → 0.2.0"
# → creates LOCAL annotated tag: v0.2.0

# ── Step 3: Push the bump commit to dev ───────────────────────────────────
git push origin dev

# ── Step 4: Open PR  dev → master  on GitHub ─────────────────────────────
#    Wait for CI to pass, then merge.

# ── Step 5: After merge, pull master ─────────────────────────────────────
git checkout master && git pull

# ── Step 6: Push the tag (this triggers release.yml) ─────────────────────
git push origin v0.2.0
#    ↑ Do NOT use --follow-tags here; only push the specific tag.
#    Pushing to master itself would be rejected by branch protection.
```

### Recovery: If You Accidentally Bumped on `master`

```bash
# Undo the bump commit and delete the local tag
git checkout master
git reset --hard origin/master
git tag -d v0.2.0

# Re-do the bump on dev
git checkout dev
bump-my-version bump minor
git push origin dev
# → then follow steps 4-6 above
```

### What Happens After Tag Push

```
git push origin v0.2.0
         │
         └─── Workflow: Release (release.yml)
                   ├── Job: ci       lint + test (guard)
                   ├── Job: build    python -m build → sdist + wheel
                   └── Job: release  gh release create v0.2.0
                                     assets: .tar.gz + .whl attached automatically
                                     release notes auto-generated from commits
```

---

## 6. Style Standards Quick Reference

| Concern | Tool | Config location |
|---|---|---|
| Line length ≤ 88 | ruff, flake8 | `pyproject.toml [tool.ruff]`, `.flake8` |
| Import order | ruff (isort) | `pyproject.toml` |
| Type annotations | mypy (strict) | `pyproject.toml [tool.mypy]` |
| Docstrings | flake8-docstrings (PEP 287 reST) | `.flake8` |

### Color Palette (Petroff 2021 — do not change)

```python
PETROFF_PALETTE = [
    "#3f90da",  # deep blue    — primary series
    "#ffa90e",  # orange       — secondary series
    "#bd1f01",  # dark red     — mean lines / reference
    "#94a4a2",  # gray         — control-limit bands
    "#832db6",  # purple
    "#a96b59",  # brown
    "#e76300",  # burnt orange
    "#b9ac70",  # khaki
    "#717581",  # slate
    "#92dadd",  # light teal
]
```

### Canvas Margin Constants (do not change)

```python
LEFT   = 0.15   # room for long Y-axis tick labels
RIGHT  = 0.95   # right edge (5% gap to prevent tick clipping)
TOP    = 0.91   # 9% reserved for Tier-3 context label
BOTTOM = 0.12   # room for X-axis title
```

---

## 7. Key Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Style storage | `DSPStyleContext` frozen dataclass | Immutability prevents accidental runtime mutations; singleton `DSP_STYLE_CONTEXT` ensures consistency |
| Three-tier positioning | `fig.canvas.draw()` + `get_window_extent()` | Pixel-accurate Tier-2 placement next to Tier-1 without character-width heuristics |
| Composite chart | `GridSpec(height_ratios=[7,3], hspace=0)` | `hspace=0` fuses panels visually; `labelbottom=False` hides upper X tick labels while keeping lines |
| `savefig` | No `bbox_inches="tight"` | `tight` overrides the carefully set `subplots_adjust` margins |
| `cycler` import | `from cycler import cycler as make_cycler` | `matplotlib.cycler` has no type stubs; direct import is fully typed |
| Style enforcement | Zero-config locked theme | No per-call overrides possible — all charts are visually consistent by default |

---

## 8. GitHub Pages (Sphinx Docs)

The live API docs are served from the `gh-pages` branch:

- **URL:** `https://penhsuanwang.github.io/scientific-plot-converter/`
- **Source:** `gh-pages` branch, root `/` (configured in repo Settings → Pages)
- **Trigger:** Automatic deploy on every push to `master` via `docs.yml`

### How It Works

```
Push to master
    └── docs.yml / build job     sphinx-build -b html docs docs/_build/html
    └── docs.yml / deploy job    peaceiris/actions-gh-pages → pushes to gh-pages branch
                                 GitHub Pages serves from gh-pages automatically
```

### Important: Do Not Track `docs/_build/`

`docs/_build/` is in `.gitignore` — never commit built HTML to the repo.
The `deploy` job rebuilds from source on every `master` push.

### Adding a New Module to the Docs

1. Create `docs/api/<module_name>.rst`:
   ```rst
   My Module
   =========
   .. automodule:: dsprinter.<module_name>
      :members:
      :show-inheritance:
   ```
2. Add `api/<module_name>` to the `toctree` in `docs/index.rst`
3. Verify: `sphinx-build -b html docs docs/_build/html -q` exits 0

---

## 9. Session History Reference

| Checkpoint | What was accomplished |
|---|---|
| `001-visualization-layout-standard.md` | Full implementation of the Advanced Data Visualization Layout Standard: `DSPStyleContext`, `CanvasBuilder`, `render_compare`, three-tier CLI flags, 17 tests, updated SRS/SDD, README, and Sphinx docs |
| `002-bug-fixes-docs-and-97-test-suite.md` | Bug fixes (output path, three-tier annotation), unit test expansion to 97 tests, README quick-start with `demo_histogram_data.csv`, `.gitignore` patterns for `.coverage`/`__pycache__` |
| `003-multi-column-hist-gh-pages-font-fixes.md` | Multi-column histogram (`--x` repeated flag), gh-pages deploy workflow, font size fixes, `docs/_build/` removed from git tracking |
| `004-ci-fixes-typography-spec-pr-setup.md` | Ticklabel auto-rotation (US-2.4), quantitative typography spec US-2.6, `axes.labelsize` 10pt→12pt bug fix, CI branch targets fixed (`main`→`dev`/`master`), PR template, pre-commit Python version fix |
