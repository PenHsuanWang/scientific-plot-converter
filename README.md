# dsprinter

A standardized Python Command-Line Interface (CLI) utility designed to generate publication-quality, "Scientific-Grade" visualizations from semiconductor manufacturing data (CSV/Parquet).

**dsprinter** moves your team from basic business intelligence charts to statistically sound "visual metrology." It enforces the **Advanced Data Visualization Layout Standard** — a high-energy physics–inspired style system — for internal reports and external whitepapers, prioritizing statistical authority, accessibility, and precision.

## Features

- **Three-Tier Typography System:** Every chart carries three structured annotation layers — a **bold** Tier-1 project/brand tag (lower-left), an *italic* Tier-2 data-status tag (same line, 75% size), and a regular-weight Tier-3 context label (upper-right, for time range / sample count).
- **Golden Margin Layout:** Canvas margins are locked at `L: 15%, R: 5%, T: 9%, B: 12%` to guarantee consistent breathing room across all plot types, regardless of tick label length.
- **Mirror Ticks:** All four chart borders carry inward-facing tick marks, enabling precise value read-off from any edge of the plot — a standard from high-energy physics publishing.
- **Petroff Color Palette:** Replaces software-default saturated colors with the Petroff (2021) palette — high-contrast, grayscale-distinguishable, and color-vision-deficiency friendly.
- **High-Performance Ingestion:** Powered by `Polars` to rapidly ingest and process massive multi-column CSV and Parquet files commonly found in Fab environments.
- **Smart Analytics:**
  - **hist1d:** Distribution Analysis with smart binning (Freedman-Diaconis rule) and optional Yield Density (PDF) normalization.
  - **trend:** Time-Series or Lot-Series analysis with automatic Control Limits (UCL/LCL at $\pm 3\sigma$) rendered as subtle shaded regions.
  - **compare:** 7:3 composite layout — primary data panel (70%) stacked above a ratio/residual panel (30%), with fused X-axes for direct alignment.

## Prerequisites

- Python 3.12 or higher.
- [uv](https://github.com/astral-sh/uv) (recommended for fast dependency management).

## Installation

Clone the repository and install the package in development mode using `uv`:

```bash
git clone https://github.com/PenHsuanWang/scientific-plot-converter
cd scientific-plot-converter
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Quick Start

The repository ships with `demo_histogram_data.csv` — 200 simulated CD measurements
from two tools (`Tool_A_CD` and `Tool_B_CD`). Use it to verify your installation:

```bash
# Single-column distribution — auto-saved to figure_out/demo_histogram_data_hist1d.pdf
dp hist1d --input demo_histogram_data.csv --x Tool_A_CD

# With full three-tier annotation and explicit output path
dp hist1d --input demo_histogram_data.csv --x Tool_A_CD \
  --project "WaferFab / CD Monitor" --status "Simulation" \
  --context "2024-Q4 · N=200" --output tool_a_dist.pdf

# Overlay two columns on the same histogram (repeat --x for each column)
dp hist1d --input demo_histogram_data.csv \
  --x Tool_A_CD --x Tool_B_CD \
  --project "WaferFab / CD Monitor" --status "Simulation" \
  --context "2024-Q4 · N=200" --output tool_overlay.pdf
```

Output files are automatically routed to `figure_out/` (created on first run if it does not exist).

## Usage

You can invoke the CLI using the `dp` command. To see all available commands and options, use the `--help` flag:

```bash
dp --help
```

### Three-Tier Annotation Flags

All commands accept three optional annotation flags that embed structured metadata directly on the canvas:

| Flag | Tier | Style | Position | Example value |
|---|---|---|---|---|
| `--project` | 1 — Brand/Project tag | **Bold** | Lower-left | `"ACME / PROC-42"` |
| `--status` | 2 — Data-status tag | *Italic* (75% size) | Next to Tier-1 | `"Preliminary"` |
| `--context` | 3 — Context label | Regular (60% size) | Upper-right | `"2024-Q1 · N=1200"` |

```bash
dp hist1d --input demo_histogram_data.csv --x Tool_A_CD \
  --project "Fab12 / CD Monitor" --status "Internal Use Only" \
  --context "2024-Q4 · N=200"
```

### 1. Distribution Analysis (`hist1d`)

Generate a 1D histogram to visually analyze yield distribution and compare lots.
Repeat `--x` to overlay multiple column distributions on the same canvas.

```bash
# Basic usage (outputs to figure_out/data_hist1d.pdf by default)
dp hist1d --input data.csv --x CD_Value

# Normalize to Yield Density (PDF) and specify custom output
dp hist1d --input process_data.parquet --x Threshold_Voltage --norm --output yield_dist.svg

# With full three-tier annotation
dp hist1d --input process_data.parquet --x Threshold_Voltage \
  --project "WaferFab / Vth Monitor" --status "Simulation" \
  --context "2024-Q4 · N=3000" --output vth_dist.pdf

# Overlay two columns — repeat --x for each series (shared bin range, Petroff colors)
dp hist1d --input demo_histogram_data.csv \
  --x Tool_A_CD --x Tool_B_CD \
  --project "WaferFab / CD Monitor" --status "Simulation" \
  --context "2024-Q4 · N=200" --output tool_overlay.pdf
```

### 2. Trend Analysis (`trend`)

Plot a metric over time or lot number to identify process drifts or excursions.

```bash
# Plot CD_Value over LotID
dp trend --input lot_summary.csv --x LotID --y CD_Value

# With annotation and custom output
dp trend --input lot_summary.csv --x LotID --y CD_Value \
  --project "Fab12 / Etch Dept" --status "Draft" \
  --context "Jan–Mar 2025" --output cd_trend.pdf
```

### 3. Comparative Analysis (`compare`)

Generate a 7:3 composite chart — a primary data panel (70%) stacked above a ratio panel (30%).
The X-axes are fused so both panels share the same scale and alignment.

```bash
# Compare two columns (ratio = y2 / y1)
dp compare --input wafer_data.csv --x LotID --y1 Target_CD --y2 Measured_CD \
  --output cd_ratio.pdf

# With three-tier annotation
dp compare --input wafer_data.csv --x LotID --y1 Target_CD --y2 Measured_CD \
  --project "Fab12 / CD Metrology" --status "Preliminary" \
  --context "2025-Q1 · N=480" --output cd_ratio_annotated.pdf
```

---

## Development

### Project Structure

```
scientific-plot-converter/
├── src/dsprinter/
│   ├── __init__.py       # package version (__version__)
│   ├── cli.py            # Typer entry points: hist1d, trend, compare (+ three-tier flags)
│   ├── data/io.py        # Polars wrappers for high-speed ingestion and validation
│   ├── stats/metrics.py  # Statistical calculations (N, μ, σ, Cpk, binning, calculate_ratio)
│   └── render/
│       ├── engine.py     # DSPStyleContext (frozen dataclass), CanvasBuilder (golden margins,
│       │                 #   mirror ticks, Petroff palette, three-tier typography)
│       └── plots.py      # render_hist1d, render_trend, render_compare (7:3 composite)
├── tests/
│   ├── test_cli.py       # CLI integration tests (hist1d, trend, compare, routing)
│   ├── test_io.py        # Data loading and format tests
│   ├── test_metrics.py   # Statistical calculation tests
│   └── test_engine.py    # Canvas rendering and typography tests (99 tests total)
├── docs/                 # Sphinx source; build with: sphinx-build -b html docs docs/_build/html
│   ├── conf.py
│   ├── index.rst
│   └── api/              # autodoc stubs for all modules
├── figure_out/           # ← auto-created at runtime; in .gitignore
├── .pre-commit-config.yaml
├── .gitignore
├── tox.ini
├── pyproject.toml        # version source of truth + [tool.bumpversion] config
└── .github/
    └── workflows/
        ├── ci.yml        # runs on push/PR to main
        └── release.yml   # runs on v* tags → GitHub Release
```

---

### Building the API Documentation (Sphinx)

The `docs/` directory contains a Sphinx project with autodoc stubs for all modules.

```bash
# One-time: install the package first (autodoc imports the live code)
source .venv/bin/activate

# Build HTML docs
sphinx-build -b html docs docs/_build/html

# Open in browser
open docs/_build/html/index.html
```

---

### Step 1 — One-Time Local Setup

After cloning and installing dependencies (see [Installation](#installation)), register the pre-commit hooks into your local git repository:

```bash
pre-commit install
```

This installs a `.git/hooks/pre-commit` script that automatically runs all quality checks every time you run `git commit`.

> **Note:** The `mypy` hook uses `language: system`, meaning it resolves imports from your active virtual environment. Always activate `.venv` before committing.

---

### Step 2 — Write Code

The codebase enforces two style standards:

| Standard | Scope | Tool |
|---|---|---|
| [PEP 8](https://peps.python.org/pep-0008/) | Formatting, naming, line length (≤88 chars) | `ruff`, `flake8` |
| [PEP 287](https://peps.python.org/pep-0287/) | reStructuredText docstrings | `flake8-docstrings` |

Every public function and class must carry a reST docstring:

```python
def compute_stats(data: pl.Series) -> dict[str, float]:
    """Compute descriptive statistics for a data series.

    :param data: A Polars Series of numeric measurements.
    :type data: pl.Series
    :returns: Mapping of statistic name to value (n, mean, std, cpk).
    :rtype: dict[str, float]
    :raises ValueError: If the series is empty.
    """
```

---

### Step 3 — Commit (pre-commit hooks fire automatically)

When you run `git commit`, the following hooks execute in order:

```
git commit -m "feat: add new plot type"
```

| Hook | What it checks / fixes |
|---|---|
| `trailing-whitespace` | Strips trailing spaces from all files |
| `end-of-file-fixer` | Ensures every file ends with a single newline |
| `check-yaml` | Validates YAML syntax |
| `check-added-large-files` | Rejects files > 500 KB |
| `ruff --fix` | Fast PEP 8 lint; auto-fixes safe issues |
| `flake8` | PEP 8 style + PEP 287 docstring enforcement on `src/` and `tests/` |
| `mypy src/` | Strict static type checking across the entire package |

If any hook reports an error, the commit is **blocked**. Fix the reported issues and re-stage your files:

```bash
git add -u
git commit -m "feat: add new plot type"   # hooks re-run
```

---

### Step 4 — Run the Full Check Suite Locally with `tox`

Before pushing, reproduce the exact CI environment locally using `tox`. This catches any issues that only appear in an isolated, freshly built package:

```bash
# Run both environments (lint + test)
tox

# Or target a single environment
tox -e lint    # ruff + flake8 + mypy
tox -e test    # pytest --cov=dsprinter
```

`tox` builds a source distribution from `pyproject.toml`, installs it into an isolated virtualenv, then runs the commands — mirroring exactly what GitHub Actions does.

Expected output on a clean codebase:

```
lint: OK ✔
test: OK ✔
  congratulations :)
```

---

### Step 5 — Push and CI

Once your commit is pushed to GitHub, the CI pipeline (`.github/workflows/ci.yml`) triggers automatically on every push and pull request to `main`.

#### CI Jobs

```
push / pull_request
        │
        ├─── Job: pre-commit
        │         ├── Install project deps (needed by mypy system hook)
        │         ├── Install pre-commit
        │         └── pre-commit run --all-files
        │
        └─── Job: tox (matrix)
                  ├── tox -e lint   →  ruff + flake8 + mypy
                  └── tox -e test   →  pytest --cov=dsprinter
```

The two tox matrix jobs run in parallel. All three jobs must pass before a pull request can be merged.

---

### Running Individual Tools Manually

```bash
# Ruff (fast lint)
ruff check src tests

# Flake8 (PEP 8 + PEP 287 docstrings)
flake8 src tests

# mypy (strict types)
mypy src

# pytest with coverage
pytest --cov=dsprinter --cov-report=term-missing

# Run all pre-commit hooks without committing
pre-commit run --all-files
```

---

### Complete Developer Workflow at a Glance

```
1. git clone + uv pip install -e ".[dev]"   # one-time setup
2. pre-commit install                         # one-time: register git hooks
        ↓
3. Edit source code in src/dsprinter/
        ↓
4. git add <files>
        ↓
5. git commit -m "..."
   └── pre-commit hooks run automatically
       trailing-whitespace ✔  end-of-file-fixer ✔  check-yaml ✔
       ruff --fix ✔  flake8 ✔  mypy ✔
       → blocked if any check fails; fix and re-stage
        ↓
6. tox                  # optional but recommended before push
   └── lint ✔  test ✔
        ↓
7. git push origin <branch>
        ↓
8. GitHub Actions CI
   ├── pre-commit (all hooks)  ✔
   ├── tox -e lint             ✔
   └── tox -e test             ✔
        ↓
9. Open / merge Pull Request
```
---

## Versioning

This project follows [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`) and uses
[bump-my-version](https://github.com/callowayproject/bump-my-version) to keep the version string
consistent across all files and to create annotated git tags automatically.

### Version sources (kept in sync automatically)

| File | Field |
|---|---|
| `pyproject.toml` | `version = "..."` under `[project]` and `current_version` under `[tool.bumpversion]` |
| `src/dsprinter/__init__.py` | `__version__ = "..."` |

**Never edit these manually.** Always use the `bump-my-version` commands below.

### How to cut a release

**Step 1 — Decide the bump type**

| Change type | Command | Example |
|---|---|---|
| Bug fix / patch | `bump-my-version bump patch` | `0.1.0` to `0.1.1` |
| New feature, backward-compatible | `bump-my-version bump minor` | `0.1.0` to `0.2.0` |
| Breaking change | `bump-my-version bump major` | `0.1.0` to `1.0.0` |

**Step 2 - Run the bump command** (working tree must be clean)

```bash
# Activate your virtual environment first
source .venv/bin/activate

# Example: patch release
bump-my-version bump patch
```

This will:

1. Update `version` in `pyproject.toml` and `__version__` in `src/dsprinter/__init__.py`
2. Create a git commit: `Bump version: 0.1.0 to 0.1.1`
3. Create an annotated git tag: `v0.1.1`

The commit skips pre-commit hooks (`commit_args = "--no-verify"`) because the version bump
itself is always valid.

**Step 3 - Push the commit and tag together**

```bash
git push --follow-tags
```

`--follow-tags` pushes both the commit and the annotated tag in one command.

### What happens on GitHub after the tag is pushed

The tag push triggers `.github/workflows/release.yml`:

```
tag push v*.*.*
        |
        +-- Job: ci          (lint + test must pass)
        |         +-- tox -e lint   ->  ruff + flake8 + mypy
        |         +-- tox -e test   ->  pytest --cov=dsprinter
        |
        +-- Job: build       (needs: ci)
        |         +-- python -m build  ->  dist/ sdist + wheel
        |         +-- upload dist/ as artifact
        |
        +-- Job: release     (needs: build)
                  +-- gh release create v*.*.*
                      +-- title: "Release v*.*.*"
                      +-- release notes: auto-generated from commits
                      +-- assets: sdist (.tar.gz) + wheel (.whl)
```

The release is visible at **GitHub > Releases**. No manual upload steps are needed.

### Preview a bump without changing anything

```bash
bump-my-version bump patch --dry-run --verbose
```

This shows exactly which lines in which files would change, what commit message and tag would be
created - without writing anything to disk.
