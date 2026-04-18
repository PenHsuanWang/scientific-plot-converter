# Software Design Document (SDD): dsprinter

## 1. Introduction & Scope
- **Purpose:** A standardized Python CLI utility to generate publication-quality, "Scientific-Grade" visualizations from semiconductor manufacturing data (CSV/Parquet). It enforces a uniform corporate/research style for internal reports and external whitepapers, moving users from basic BI charts to "visual metrology."
- **System Boundaries:**
  - **In-Scope:** Parsing tabular data, calculating statistical indicators (Mean, Sigma, Cpk), generating strict vector graphics (PDF/SVG), enforcing standardized themes, handling declarative CLI arguments, and supporting YAML-based recipe templates.
  - **Out-of-Scope:** Interactive GUI dashboards, data warehousing, fetching data directly from Fab tools via network protocols (assumes data is provided locally as flat files).
- **Stakeholders:** Product Managers, Data Science Researchers, Yield Enhancement Engineers, and Process Integration Engineers.

## 2. System Architecture (HLD)
- **Deployment Strategy:** Local Python Command-Line Interface (CLI) tool. Distributed as a standard Python package installable via `pip` or managed via `uv`.
- **High-Level Diagram:**
  - `CLI Interface` -> `Configuration Manager` -> `Data Ingestion Engine` -> `Statistical Engine` -> `Plotting & Styling Engine` -> `Vector Exporter`
- **External Dependencies:**
  - Runtime: Python 3.12+
  - CLI Framework: `typer` (for declarative parsing and auto-generated help menus)
  - Data Processing: `polars` (for high-speed multi-file ingestion), `numpy`, `scipy` (for Cpk and distribution metrics)
  - Rendering Engine: `matplotlib` combined with `proplot` (for rigorous subplot alignment and scientific styling)
  - Configuration: `pyyaml` (for template recipes)

## 3. Domain-Driven Design (DDD) Mapping
- **Bounded Contexts:**
  - `CLI & Configuration`: Responsible for parsing user intent, merging CLI flags with YAML templates, and locking global settings.
  - `Data Pipeline`: Responsible for file reading, schema validation, and missing data imputation/filtering.
  - `Metrology Plotting`: Responsible for mapping data to visual primitives, applying statistical overlays, and enforcing the "Fab-Header" layout.
  - `Composite Chart`: Responsible for the `dp compare` two-panel layout, shared axis alignment, and ratio/residual computation.
  - `Temporal State Rendering`: Responsible for parsing categorical state timelines, detecting rendering mode (exact Gantt bars vs. aggregated bins), mapping categorical states to color assignments, rendering faceted multi-panel layouts, applying global event overlays across all panels, and computing per-channel summary statistics.
  - `Transition Analytics Rendering`: Responsible for computing consecutive state-pair counts from sorted state logs, row-normalizing counts into conditional probabilities, and rendering the dual-panel heatmap with log-scale colormaps, diagonal cell highlights, and in-cell annotations.
- **Aggregates & Entities:**
  - `PlotJob`: The main aggregate root representing a single CLI execution, containing the dataset references, plot parameters, and final output destinations.
  - `DSPStyleContext`: Entity enforcing the locked typography hierarchy (three-tier), golden margin ratios, mirror-tick axis configuration, Petroff palette, legend placement rules, and the `gantt_min_px_width` aggregation threshold constant (default 2 px). All `Plotter` subclasses receive a `DSPStyleContext` at construction time and must not override any of its locked properties.
  - `GanttJob`: Aggregate root for a single `dp gantt` CLI invocation. Contains references to the parsed `ChannelData` list, an optional list of `EventOverlay` objects, an optional `DomainPalette`, the shared time range, and the output destination path.
  - `ChannelData`: Value object holding one channel's complete state record sequence as `list[tuple[datetime, datetime, str]]` (start, end, state_label) plus the channel name string.
  - `EventOverlay`: Value object representing a global event. Either a point event `{timestamp: datetime, label: str}` or a duration event `{start: datetime, end: datetime, label: str}`, plus rendering metadata (line style, color, alpha).
  - `DomainPalette`: Value object mapping `dict[str, str]` (state_label → hex color). Validated at construction time: each color pair must satisfy a minimum grayscale luminance contrast ratio of 3:1; violations emit a warning but do not block construction.
  - `TransitionJob`: Aggregate root for a single `dp transition` CLI invocation. Contains the input DataFrame reference, column name bindings (`channel_col`, `time_col`, `state_col`), the computed `TransitionMatrix`, and output destination path.
  - `TransitionMatrix`: Value object holding the square count matrix as `np.ndarray` (int64), the ordered state labels as `list[str]`, and the derived row-normalized probability matrix as `np.ndarray` (float64). Constructed once after data pre-processing and passed immutably to the renderer.

## 4. Component Design (LLD)
- **Microservices / Modules:**
  - `dsprinter.cli`: Typer application entry points (e.g., `@app.command() def hist1d(...)`, `@app.command() def compare(...)`).
  - `dsprinter.data.io`: Polars wrappers to load and validate CSV/Parquet.
  - `dsprinter.stats.metrics`: Core functions calculating $N$, $\mu$, $\sigma$, $C_{pk}$, smart binning rules, and ratio/residual computation for the compare panel.
  - `dsprinter.render.engine`: Abstraction layer over Matplotlib/Proplot. Contains:
    - `DSPStyleContext`: Immutable value object holding all locked styling constants — font family, three-tier size ratios (1.0x / 0.75x / 0.60x), golden margin values (L=0.15, R=0.05, T=0.09, B=0.12), Petroff color sequence, and tick direction.
    - `CanvasBuilder`: Applies `DSPStyleContext` to a Matplotlib `Figure`, sets margins via `fig.subplots_adjust`, configures `rcParams` (font, tick direction=`in`, top/right tick visibility), and renders the three-tier annotation layer.
  - `dsprinter.render.plots`: Specific implementation classes:
    - `HistogramPlotter`: Renders `hist1d` on a single-panel canvas.
    - `TrendPlotter`: Renders `trend` on a single-panel canvas.
    - `CompositePlotter`: Renders `dp compare` using a `gridspec` with a 7:3 row height ratio. Shares the X-axis between panels via `sharex=True`. Hides upper panel X-tick labels post-render using `ax_upper.tick_params(labelbottom=False)`.
  - `dsprinter.render.gantt`: Faceted Gantt chart implementation classes:
    - `GanttPlotter`: Top-level renderer for `dp gantt`. Orchestrates channel panel construction via `GridSpec(nrows=N, hspace=0, sharex=True)`, delegates to `AggregationEngine` for mode selection, calls `EventOverlayRenderer` to paint overlays across all axes, annotates each row's right margin with per-channel statistics, and places a unified legend below the bottom panel.
    - `AggregationEngine`: Internal strategy engine. Computes `pixel_density = canvas_px_width / total_time_seconds` and compares each state's `duration_seconds` against `DSPStyleContext.gantt_min_px_width / pixel_density`. Selects either `ExactIntervalRenderer` (low density) or `BinProportionRenderer` (high density). Bin granularity (hourly vs. daily) is chosen by comparing total time span against fixed thresholds (≤ 7 days → hourly; > 7 days → daily).
    - `EventOverlayRenderer`: Applies `axvline` (dashed, high `zorder`) for point events and `axvspan` (semi-transparent fill, high `zorder`) for duration events across every shared axis in the panel stack.
  - `dsprinter.stats.metrics` (extended): New pure functions:
    - `compute_state_bins(records, bucket_size)`: Groups state records into fixed-duration time buckets and returns proportional occupancy per state per bucket.
    - `state_distribution(records)`: Returns a `dict[str, float]` mapping each state label to its percentage of total covered time for a single channel.
    - `validate_grayscale_contrast(palette)`: Checks that all adjacent pairs of hex colors in a `DomainPalette` satisfy the 3:1 luminance contrast rule; returns a list of violation tuples.
  - `dsprinter.render.transition` *(new)*: Dual-panel State Transition Matrix implementation:
    - `render_transition()`: Public entry point. Accepts a `polars.DataFrame`, column name bindings, and typography arguments. Delegates data pre-processing to `metrics`, constructs a `TransitionMatrix`, builds a `GridSpec(1, 2)` dual-panel figure via `CanvasBuilder`, and delegates each panel to private helpers.
    - `TransitionJob`: Value object capturing the CLI invocation context: input DataFrame, `channel_col`, `time_col`, `state_col`, and output path.
    - `_render_count_panel()`: Renders the left heatmap using `imshow` with `LogNorm(vmin=1)` and the `YlOrRd` colormap; appends a labeled color bar; applies diagonal cell borders via `Rectangle` patches; annotates each cell with a comma-formatted integer and luminance-inverted text color.
    - `_render_probability_panel()`: Renders the right heatmap using `imshow` with linear normalization and the `Blues` colormap; applies diagonal borders; annotates each cell with a two-decimal float and luminance-inverted text color.
    - `_draw_diagonal_borders()`: Shared helper. Iterates diagonal indices and overlays a `Rectangle` patch with `linewidth=2.5`, black edge, and `fill=False` on the provided `Axes`.
    - `_cell_text_color()`: Private helper (also exposed from `metrics.py`). Computes WCAG 2.1 relative luminance of a background hex color and returns `"#000000"` (luminance ≥ 0.179) or `"#FFFFFF"` (luminance < 0.179).
  - `dsprinter.stats.metrics` (extended for EPIC-8): New pure functions:
    - `compute_transition_matrix(df, channel_col, time_col, state_col)`: Sorts `df` by `(channel_col, time_col)`, extracts consecutive state pairs per entity, counts occurrences for each `(from_state, to_state)` pair, and returns a tuple `(count_matrix: np.ndarray, state_labels: list[str])`. States are ordered alphabetically.
    - `row_normalize_matrix(count_matrix)`: Divides each row of `count_matrix` by its row sum. Rows with a zero sum (states that never appear as a source) are returned as all-zeros without raising.
    - `cell_text_color(bg_hex)`: Computes WCAG 2.1 relative luminance of `bg_hex` and returns `"#000000"` or `"#FFFFFF"` using threshold 0.179.
- **Design Patterns:**
  - **Strategy Pattern:** For determining the plot type (`hist1d`, `trend`, `compare`, `gantt`, `transition`) and for selecting the Gantt rendering mode (`ExactIntervalRenderer` vs. `BinProportionRenderer`) inside `AggregationEngine`.
  - **Builder Pattern:** To construct the complex figure layout step-by-step (Base Canvas → Axes → Data Lines/Bars → Statistical Annotations → Three-Tier Typography Headers).
  - **Value Object Pattern:** `DSPStyleContext`, `ChannelData`, `EventOverlay`, `DomainPalette`, and `TransitionMatrix` are all constructed once and passed immutably to rendering components, preventing accidental style or data drift.
  - **Composite Shared-Axis Layout:** N equal-height Gantt row panels are constructed via `GridSpec(nrows=N, hspace=0)` with `sharex=True` across all axes. Only the bottom panel enables `labelbottom=True`; all upper panels call `tick_params(labelbottom=False)`. Mirrors the `CompositePlotter` 7:3 pattern.
  - **Dual-Panel Heatmap Layout:** Two equal-width panels are constructed via `GridSpec(1, 2, wspace=0.4)`. Each panel receives an independent `imshow` with its own normalization and colormap, followed by a `fig.colorbar()` attached to its respective `Axes`.

## 5. Data Design
- **Logical Schema:**
  - The system operates on in-memory column-oriented data structures (`polars.DataFrame`). No persistent internal schema.
- **Storage Solutions:**
  - Ephemeral memory during execution. Output is committed to the local filesystem as `.pdf` or `.svg`.
- **Data Flow:**
  1. User invokes `dp hist1d --input data.csv`.
  2. `typer` parses arguments and instantiates `PlotJob`.
  3. `polars` lazily loads `data.csv` (or eagerly if filtering is required).
  4. Statistics are computed on the requested `--x` column.
  5. The `render.engine` initializes the canvas with the `DSPStyleContext`.
  6. `render.plots` maps the data and statistics to the canvas.
  7. The figure is saved to the output path.

  **Gantt Data Flow (`dp gantt`):**
  1. User invokes `dp gantt --input data.csv --time timestamp --state status --channel entity_id`.
  2. `typer` parses arguments and instantiates `GanttJob` with optional `--events` and `--domain-palette` values.
  3. `polars` loads the CSV; schema validation confirms `--time`, `--state`, and `--channel` columns exist.
  4. `metrics.state_distribution()` and `metrics.compute_state_bins()` compute per-channel statistics and aggregation bins.
  5. `AggregationEngine` evaluates pixel density and selects `ExactIntervalRenderer` or `BinProportionRenderer`.
  6. `render.engine` initializes the canvas with `DSPStyleContext`; `CanvasBuilder` applies three-tier typography and golden margins.
  7. `GanttPlotter` builds the `GridSpec(nrows=N, hspace=0)` layout, renders one panel per channel, applies event overlays via `EventOverlayRenderer`, annotates right-margin statistics for each row, and places the unified bottom legend.
  8. The figure is saved to the output path.

  **Transition Matrix Data Flow (`dp transition`):**
  1. User invokes `dp transition --input state_log.csv --channel entity --time ts --state status`.
  2. `typer` parses arguments and instantiates `TransitionJob` with column bindings and output destination.
  3. `polars` loads the CSV; schema validation confirms `--channel`, `--time`, and `--state` columns exist.
  4. `metrics.compute_transition_matrix()` sorts the DataFrame by `(channel_col, time_col)`, extracts all consecutive state pairs per entity, counts occurrences, and returns `(count_matrix: np.ndarray, state_labels: list[str])`.
  5. `metrics.row_normalize_matrix()` produces the probability matrix; zero-sum rows are silently left as all-zeros.
  6. A `TransitionMatrix` value object is constructed from the count matrix, probability matrix, and state labels.
  7. `render.engine` initializes the canvas with `DSPStyleContext`; `CanvasBuilder` applies three-tier typography and golden margins.
  8. `render_transition()` builds a `GridSpec(1, 2, wspace=0.4)` layout. `_render_count_panel()` draws the left heatmap (`LogNorm`, `YlOrRd`); `_render_probability_panel()` draws the right heatmap (linear, `Blues`). `_draw_diagonal_borders()` overlays `Rectangle` patches on both panels. Each cell receives in-cell annotation with luminance-inverted text.
  9. The figure is saved to the output path.

## 6. UI & Interaction Design
- **Key User Journeys:**
  - **Discovery:** User runs `dp --help` and receives a rich, organized terminal UI describing plot types and flags.
  - **Generation:** User runs a declarative command `dp trend --x time --y CD --norm --style internal_confidential`. The CLI provides a brief progress indicator and outputs the file path of the generated PDF.
  - **Gantt Generation:** User runs `dp gantt --input ops_log.csv --time ts --state health --channel service_name --events events.json --output report.pdf`. The CLI validates columns, selects rendering mode automatically, and produces a multi-panel PDF with per-row statistics and a unified bottom legend.
  - **Transition Matrix Generation:** User runs `dp transition --input ops_log.csv --channel service --time ts --state health --project "Ops" --status "Draft" --output report.pdf`. The CLI validates columns, computes the transition matrix, and produces a dual-panel PDF with count and probability heatmaps, diagonal borders, in-cell annotations, and a color bar on each panel.
- **State Management:** The application is entirely stateless between executions.

## 7. Technical Specifications & Non-Functional Requirements
- **Performance:** `polars` guarantees fast I/O and processing, capable of handling gigabytes of metrology data efficiently. Plot rendering should complete within seconds. The `AggregationEngine` aggregation heuristic must run in O(N log N) time relative to total state records, sustaining the seconds-level performance envelope for datasets with 10,000+ records per channel.
- **Reliability:** "Zero-Config Styling" prevents the user from breaking the layout. The tool must gracefully handle and log errors for missing columns or mathematically invalid data (e.g., calculating $C_{pk}$ on zero variance, or division-by-zero in the ratio panel) without crashing abruptly. Gantt charts with channels containing no records within the visible time range must render an empty panel with a "No Data" annotation rather than raising an exception.
- **Visual Accuracy:** "Vector First" requirement mandates that all geometric primitives (lines, hatches, fonts) are infinitely scalable. Aliasing and pixelation are strictly prohibited for production outputs. The 2-pixel aggregation threshold in `DSPStyleContext.gantt_min_px_width` must be evaluated against the canvas's physical pixel width (figure width in inches × DPI), not logical units.
- **Style Integrity:** `DSPStyleContext` constants (margin ratios, font size ratios, Petroff palette, tick direction, `gantt_min_px_width`) are defined as module-level frozen values and must not be modifiable at runtime. Domain palette overrides supplied via `--domain-palette` are runtime-only and must not mutate `DSPStyleContext`; violations raise a `TypeError` at construction time.
- **Accessibility:** The Petroff palette must maintain a minimum luminance contrast ratio of 3:1 between adjacent series when converted to grayscale, ensuring legibility in monochrome print and for readers with deuteranopia or protanopia. The same 3:1 invariant is enforced on `DomainPalette` at construction time via `metrics.validate_grayscale_contrast()`; violations emit a `UserWarning` but do not block rendering.

## 8. Key Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Style storage | `DSPStyleContext` frozen dataclass | Immutability prevents accidental runtime mutations; singleton `DSP_STYLE_CONTEXT` ensures consistency across all plot types |
| Three-tier positioning | `fig.canvas.draw()` + `get_window_extent()` | Pixel-accurate Tier-2 placement next to Tier-1 without character-width heuristics |
| Composite chart | `GridSpec(height_ratios=[7,3], hspace=0)` | `hspace=0` fuses panels visually; `labelbottom=False` hides upper X tick labels while keeping lines |
| `savefig` | No `bbox_inches="tight"` | `tight` overrides the carefully set `subplots_adjust` margins |
| `cycler` import | `from cycler import cycler as make_cycler` | `matplotlib.cycler` has no type stubs; direct import is fully typed |
| Style enforcement | Zero-config locked theme | No per-call overrides possible — all charts are visually consistent by default |
| Faceted Gantt layout | `GridSpec(nrows=N, hspace=0)` with `sharex=True` | `hspace=0` fuses panels visually; `labelbottom=False` on upper rows suppresses redundant X labels while preserving tick lines; mirrors the `CompositePlotter` 7:3 split pattern |
| Aggregation mode selection | Pixel-density heuristic in `AggregationEngine` | Zero-config requirement mandates no user flag; `canvas_px_width / time_range_seconds` provides a DPI-independent density metric; bucket granularity (hourly vs. daily) is driven by a fixed 7-day span threshold |
| Domain palette validation | Grayscale luminance contrast check at `DomainPalette` init | Maintains the Petroff accessibility invariant (≥ 3:1) even when users supply custom colors; warning-not-error design allows rendering to continue for exploratory use |
| Event overlay z-ordering | `zorder` set above all Gantt artists on `EventOverlayRenderer` | Guarantees overlay visibility regardless of state bar opacity or aggregation bin fill; prevents z-order collisions between overlays and proportional stacked bars |
| Transition dual-panel layout | `GridSpec(1, 2, wspace=0.4)` | 1:1 equal-width panels; `wspace=0.4` provides breathing room for color bars without distorting heatmap aspect ratios |
| Count panel color scale | `LogNorm(vmin=1)` with `YlOrRd` colormap | Log normalization ensures single-occurrence transitions remain visible alongside million-count transitions; `vmin=1` prevents `log(0)` errors for zero cells |
| Probability panel color scale | Linear `Normalize(vmin=0, vmax=1)` with `Blues` colormap | Probability is bounded [0, 1] so linear scale is both correct and intuitive; cool `Blues` contrasts the warm `YlOrRd` count panel to prevent cognitive cross-contamination |
| Diagonal cell highlighting | `matplotlib.patches.Rectangle` with `linewidth=2.5`, black edge, `fill=False` | Patch overlays are resolution-independent and composited above `imshow` fill; no pixel-level rounding; consistent with the `zorder` pattern used in `EventOverlayRenderer` |
| Cell luminance inversion | WCAG 2.1 relative luminance threshold 0.179 | Same formula and constant used by `validate_grayscale_contrast()` — reuses `metrics.cell_text_color()` to maintain a single implementation of luminance logic across the codebase |
| Transition data pre-processing | Sort by `(channel_col, time_col)` before pair extraction | Polars row order is not guaranteed to equal temporal order; sorting ensures consecutive pairs reflect actual state transitions, not CSV row adjacency |
