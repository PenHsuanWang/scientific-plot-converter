# Software Requirements Specification (SRS): dsprinter

## 1. Product Overview
- **Product Name:** dsprinter
- **Business Goal:** To provide a standardized Python CLI utility that generates publication-quality, "Scientific-Grade" visualizations from Fab CSV data, enforcing a uniform corporate/research style for internal reports and external whitepapers. This moves the organization from standard BI charts to statistically sound "visual metrology."
- **Target Audience:** Data Science Researchers, Yield Enhancement Engineers, Product Managers, and Process Integration Engineers in semiconductor manufacturing.

## 2. Epics & User Stories

### EPIC-1: CLI Foundation & Data Ingestion
**Description:** Establish the core command-line interface and the capability to rapidly ingest and process large multi-column semiconductor data files.

#### USER STORY-1.1: Standardized Data Loading
- **User Story:** As a Data Science Researcher, I want to load multi-column CSV and Parquet files via the CLI so that I can process large Fab datasets efficiently.
- **Acceptance Criteria (BDD Format):**
  - **Scenario 1:** Successful file load
    - **Given** a valid, formatted CSV file path provided via the `--input` flag
    - **When** the CLI command is executed
    - **Then** the system successfully ingests the data into memory using Polars without errors.
  - **Scenario 2:** Missing file handling
    - **Given** an invalid or non-existent file path
    - **When** the CLI command is executed
    - **Then** the system outputs a clear error message indicating the file was not found and exits gracefully.
- **Business Rules:** The system must handle missing data (e.g., NaNs in specific columns) based on user-defined mapping flags or skip rows gracefully.

### EPIC-2: Core "Scientific Style" Engine
**Description:** Enforce strict, zero-config typography, layout, and scientific styling for all generated plots to ensure corporate uniformity and publication readiness.

#### USER STORY-2.1: Zero-Config Typography and Styling
- **User Story:** As a Yield Enhancement Engineer, I want the tool to automatically apply locked font sizes, color-blind friendly palettes, and vector output formats so that my plots are always publication-quality without manual tweaking.
- **Acceptance Criteria (BDD Format):**
  - **Scenario 1:** Enforced vector output
    - **Given** a successful plot generation command
    - **When** the output file is created
    - **Then** the file is strictly formatted as `.pdf` or `.svg` to ensure zero pixelation.
  - **Scenario 2:** Consistent typography
    - **Given** any standard plot type
    - **When** the plot is rendered
    - **Then** the axes, legends, and titles are locked to a 10pt/12pt Arial/Helvetica font.
- **Business Rules:** Default color scales must avoid "rainbow" palettes and prioritize high-contrast, accessible textures (like hatching).

#### USER STORY-2.2: Three-Tier Typography Hierarchy
- **User Story:** As a Product Manager, I want every generated plot to automatically display a three-tier text hierarchy so that all charts carry consistent brand identity, data maturity status, and contextual metadata without any manual annotation.
- **Acceptance Criteria (BDD Format):**
  - **Scenario 1:** Tier-1 Brand/Project Tag rendered (Bold, top-left)
    - **Given** a project name is supplied via CLI flag `--project` or YAML recipe
    - **When** any plot is generated
    - **Then** the project/company identifier is rendered **bold** in the top-left corner of the canvas (inside or outside the plot frame).
  - **Scenario 2:** Tier-2 Status Tag rendered (Italic, 75-80% size, after Tier-1)
    - **Given** a status label is supplied via CLI flag `--status` (e.g., `"Internal Use Only"`, `"Preliminary"`, `"Draft"`, `"Simulation"`)
    - **When** the plot is rendered
    - **Then** the status label appears in *italic* immediately after the Tier-1 tag, at 75–80% of the Tier-1 font size.
  - **Scenario 3:** Tier-3 Context Info rendered (Regular, ~60% size, top-right)
    - **Given** context metadata is supplied via CLI flags `--context` (e.g., `"2024-Q3 | N=1000"`, `"Source: Fab-A"`)
    - **When** the plot is rendered
    - **Then** the context string appears in regular weight at the top-right corner (outside the plot frame), at approximately 60% of the Tier-1 font size.
  - **Scenario 4:** Missing optional metadata
    - **Given** only `--project` is supplied and `--status` / `--context` are omitted
    - **When** the plot is rendered
    - **Then** Tier-2 and Tier-3 zones are left empty without visual artifacts or layout shift.
- **Business Rules:** All three tiers use the same sans-serif font family (Helvetica / Arial / Noto Sans). Tier sizing ratios are locked: Tier-1 = 1.0x base, Tier-2 = 0.75–0.80x, Tier-3 = 0.60x. These ratios cannot be overridden by user input.

#### USER STORY-2.3: Golden Margin Canvas Layout
- **User Story:** As a Data Science Researcher, I want the plot engine to automatically apply precise margin ratios so that every chart has professional visual breathing room, Y-axis numbers never clip the frame, and the top margin is reserved for metadata tags.
- **Acceptance Criteria (BDD Format):**
  - **Scenario 1:** Correct margins applied to every plot
    - **Given** any plot type is generated (hist1d, trend, or compare)
    - **When** the canvas is initialized
    - **Then** the figure margins are locked to: Left = 15%, Bottom = 12%, Top = 8–10%, Right = 5% of the total canvas size.
  - **Scenario 2:** Top margin reserved exclusively for Tier-3 context metadata
    - **Given** a plot with the top margin applied
    - **When** the Tier-3 context string is rendered
    - **Then** it is positioned entirely within the top margin area and does not overlap the plot frame.
- **Business Rules:** Margin ratios are zero-config and cannot be modified by the user. This guarantees layout consistency across all output files regardless of canvas size.

#### USER STORY-2.4: Mirror Ticks & Axis Title Offset
- **User Story:** As a Process Integration Engineer, I want all four sides of the plot frame to have inward-pointing tick marks, and axis titles to be offset at a precise distance from the tick labels, so that any value on the chart can be read accurately from any edge.
- **Acceptance Criteria (BDD Format):**
  - **Scenario 1:** Four-sided mirror ticks
    - **Given** any plot is generated
    - **When** the axes are rendered
    - **Then** tick marks appear on all four sides of the plot frame (top, bottom, left, right), and all ticks point **inward** toward the data area.
  - **Scenario 2:** Axis title offset — differentiated for X and Y
    - **Given** an axis with tick labels and a title
    - **When** the axis is rendered
    - **Then** the X-axis title is padded 1.1 × base font height (≈ 11 pt) from the tick labels, and the Y-axis title is padded 1.4 × base font height (≈ 14 pt) to accommodate scientific-notation exponents (e.g., ×10³) without overlap. Both titles are centred along their respective axis lines.
  - **Scenario 3:** Axis unit format
    - **Given** an axis label is defined (e.g., `Revenue`)
    - **When** the unit is provided (e.g., `M USD`)
    - **Then** the label is rendered as `Revenue [M USD]` using square-bracket unit notation.
  - **Scenario 4:** X-axis tick label auto-rotation
    - **Given** a plot with X-axis tick labels that either (a) would visually overlap adjacent labels due to crowding, or (b) exceed 6 characters in length (e.g., datetime strings such as `"2024-01-01"`)
    - **When** the axes are finalized before the output file is written
    - **Then** all X-axis tick labels are rotated 45° (right-aligned to the tick mark) to prevent visual crowding. Y-axis tick labels are never auto-rotated.
  - **Scenario 5:** Tick label font size matches body text
    - **Given** any plot is generated
    - **When** the axes are rendered
    - **Then** X-axis and Y-axis tick labels are rendered at `base_font_size` (10 pt), consistent with the axes label font size specified in US-2.1.
- **Business Rules:** Mirror tick application is automatic and zero-config. Top/right ticks display tick lines only, with no duplicate numeric labels. X-axis tick labels are auto-rotated to `tick_label_max_rotation` (45°) when bounding-box overlap is detected or when any label exceeds `tick_label_rotation_threshold` (6 characters); this is zero-config and cannot be disabled by the user.

#### USER STORY-2.5: Petroff-Compliant Color Palette
- **User Story:** As a Data Science Researcher, I want DSPrinter to use a Petroff-principles color palette so that all plots remain legible in both color and grayscale print, and are accessible to colorblind readers.
- **Acceptance Criteria (BDD Format):**
  - **Scenario 1:** Default palette applied to all series
    - **Given** a plot with multiple data series or categories
    - **When** the plot is rendered
    - **Then** colors are drawn from the locked Petroff-inspired palette: dark blue, orange, dark red, gray (and extended variants), in that priority order.
  - **Scenario 2:** No red-green contrast used
    - **Given** any plot with two or more data series
    - **When** the plot is rendered
    - **Then** no adjacent series use a pure red vs. pure green contrast combination.
  - **Scenario 3:** Grayscale distinguishability
    - **Given** the output PDF is converted to grayscale
    - **When** the chart is inspected
    - **Then** all data series remain visually distinct through differing luminance levels.
- **Business Rules:** The Petroff palette is the sole default palette and cannot be substituted via CLI flags. Software-default high-saturation palettes (e.g., Matplotlib tab10) are strictly prohibited.

#### USER STORY-2.6: Axis Typography Quantification (CMS / HEP Reference)
- **User Story:** As a Data Science Researcher, I want all axis titles, tick labels, and legends to follow a precise, documented size hierarchy derived from HEP/CMS publication standards so that DSPrinter output matches the visual authority of CERN-style figures.
- **Acceptance Criteria (BDD Format):**
  - **Scenario 1:** Axis title is visually larger than tick labels
    - **Given** any plot is generated
    - **When** the axes are rendered
    - **Then** the axis title font size (12 pt) is strictly larger than the tick label font size (10 pt), maintaining a clear title-above-data visual hierarchy.
  - **Scenario 2:** Bold weight is exclusive to the Tier-1 brand tag
    - **Given** any generated plot containing axes, tick labels, legend entries, Tier-2, and Tier-3 annotation text
    - **When** the output is inspected
    - **Then** only the Tier-1 brand/project tag uses Bold weight; all other elements (axis titles, tick labels, legend text, Tier-2 status, Tier-3 context, stats box) strictly use Regular weight, ensuring the brand tag is the sole visual anchor and data-carrying text remains neutral.
  - **Scenario 3:** Composite chart panels render at identical absolute font sizes
    - **Given** a 7:3 composite (compare) chart is generated
    - **When** the upper main panel and lower ratio panel are both inspected
    - **Then** axis titles and tick labels in both panels are rendered at identical absolute point sizes. (Unlike ROOT/CMS where relative-to-pad-height sizing requires a `1 / PadHeightRatio` correction coefficient, DSPrinter uses absolute pt sizing so no compensation is needed — both panels are automatically uniform.)
- **Business Rules:** The following font size table is locked and zero-config. Values are mapped from the CMS/HEP relative-percentage convention (where size is expressed as a fraction of pad/canvas height) to DSPrinter absolute point sizes for a standard 8 × 6 inch canvas.

  | Element                | Weight     | DSPrinter (pt) | CMS/HEP (% canvas ht) | Ratio to base |
  |------------------------|------------|:------------:|:---------------------:|:-------------:|
  | Axis title (X and Y)   | Regular    | 12 pt        | ≈ 5 %                 | 1.2 ×         |
  | Tick labels (X and Y)  | Regular    | 10 pt        | ≈ 4 %                 | 1.0 × (base)  |
  | Legend text            | Regular    | 10 pt        | ≈ 4 %                 | 1.0 ×         |
  | Stats box text         | Regular    | 10 pt        | ≈ 4 %                 | 1.0 ×         |
  | Tier-1 brand / project | **Bold**   | 14 pt        | ≈ 7.5 %               | 1.4 ×         |
  | Tier-2 status tag      | *Italic*   | 10.8 pt      | ≈ 5.7 % (75 % of T1)  | 1.08 ×        |
  | Tier-3 context info    | Regular    | 8.4 pt       | ≈ 4.5 %               | 0.84 ×        |

  Bold weight is **strictly reserved** for the Tier-1 brand tag only. All other text elements use Regular weight regardless of semantic importance.

### EPIC-3: Standard Plot Types (Phase 1)
**Description:** Implement the primary visualization types required for daily semiconductor analysis: Distribution Analysis (hist1d) and Time/Lot-Series (trend).

#### USER STORY-3.1: Distribution Analysis (hist1d)
- **User Story:** As a Process Integration Engineer, I want to generate a 1D histogram of a specific metric so that I can visually analyze the yield distribution and compare lots.
- **Acceptance Criteria (BDD Format):**
  - **Scenario 1:** Basic filled histogram
    - **Given** the `hist1d` command with a valid `--x [column]`
    - **When** the plot is generated
    - **Then** a histogram is rendered with automatically calculated smart binning to avoid aliasing.
  - **Scenario 2:** Normalized Yield Density overlay
    - **Given** the `hist1d` command with the `--norm` flag
    - **When** the plot is generated
    - **Then** the Y-axis represents Probability Density (Yield Density) instead of raw counts.
- **Business Rules:** Smart binning algorithms must ensure no gaps in continuous semiconductor distributions.

#### USER STORY-3.2: Trend Analysis (trend)
- **User Story:** As a Yield Enhancement Engineer, I want to plot a metric over time or lot number so that I can identify process drifts or excursions.
- **Acceptance Criteria (BDD Format):**
  - **Scenario 1:** Time-series with Control Limits
    - **Given** the `trend` command with valid `--x [time/lot]` and `--y [metric]` columns
    - **When** the plot is generated
    - **Then** the time-series line is plotted, and Control Limits (UCL/LCL) are rendered as subtle shaded regions.
- **Business Rules:** Control Limits must not distract from the data; they should use shaded alpha regions rather than bright, solid lines.

### EPIC-4: Metadata, Annotations & Layout (The CERN Style)
**Description:** Implement the strict "CERN Style" layout, prioritizing statistical indicators, Fab headers, and contextual metadata directly on the canvas.

#### USER STORY-4.1: The "Fab-Header" Metadata Block
- **User Story:** As a Product Manager, I want standardized metadata blocks (Technology Node, Layer, Tool ID, Date) rendered on the plot so that context is never lost during quarterly reviews.
- **Acceptance Criteria (BDD Format):**
  - **Scenario 1:** Rendering the Top-Right Header
    - **Given** valid metadata arguments provided via CLI flags or config
    - **When** the plot is generated
    - **Then** a standardized metadata block is rendered in the top-right corner.
  - **Scenario 2:** Statistical Indicators Legend
    - **Given** any plot type
    - **When** the plot is generated
    - **Then** a non-obtrusive Legend Box automatically calculates and displays Sample Size (N), Mean (μ), Sigma (σ), and Cpk on the canvas.
- **Business Rules:** Annotations for Status (e.g., INTERNAL ONLY, DRAFT) must always be placed in the Top-Left corner.

### EPIC-6: Composite Chart Architecture (7:3 Split Layout)
**Description:** Provide a dedicated `dp compare` subcommand that renders a two-panel composite figure — a main data panel (70% height) stacked above a ratio/residual panel (30% height) — enabling direct visual comparison of data vs. prediction or period-over-period change.

#### USER STORY-6.1: `dp compare` Subcommand
- **User Story:** As a Yield Enhancement Engineer, I want to run `dp compare` with two data series so that I can see the primary distributions alongside their residuals or ratio in a single, publication-ready figure without any manual layout work.
- **Acceptance Criteria (BDD Format):**
  - **Scenario 1:** Two-panel composite figure generated
    - **Given** the `dp compare` command with valid `--x [column]`, `--y1 [series_a]`, and `--y2 [series_b]` flags
    - **When** the command is executed
    - **Then** a composite figure is generated with the main panel occupying 70% of the canvas height and the ratio/residual panel occupying the remaining 30%.
  - **Scenario 2:** X-axes are pixel-perfect aligned
    - **Given** a composite figure is rendered
    - **When** the output file is inspected
    - **Then** the X-axis data range and tick positions are identical across both panels, with no horizontal offset between the upper and lower frames.
  - **Scenario 3:** Upper panel X-axis tick labels are hidden
    - **Given** a composite figure is rendered
    - **When** the upper panel is inspected
    - **Then** the X-axis tick **lines** are present (preserving frame structure) but the numeric/text **labels** are hidden, so the two panels appear visually fused.
  - **Scenario 4:** Lower panel Y-axis label describes the derived metric
    - **Given** the `--ratio-label` flag is optionally supplied (e.g., `"Data / MC"` or `"Residual [σ]"`)
    - **When** the plot is rendered
    - **Then** the lower panel Y-axis uses that label; if omitted, it defaults to `"Ratio"`.
  - **Scenario 5:** Missing second series
    - **Given** only `--y1` is provided and `--y2` is omitted
    - **When** the command is executed
    - **Then** the CLI exits with a clear error message: `"dp compare requires both --y1 and --y2 arguments."` and no file is created.
- **Business Rules:**
  - The 70/30 height split is locked and zero-config; it cannot be adjusted via CLI flags.
  - All three-tier typography, golden margins, mirror ticks, and Petroff palette rules from EPIC-2 apply automatically to both panels.
  - The lower panel ratio/residual is computed as `y1 / y2`; the caller is responsible for ensuring the series are comparable.

### EPIC-5: Templates & Configuration
**Description:** Allow users to save and reuse common configurations via YAML recipes.

#### USER STORY-5.1: YAML Recipe Execution
- **User Story:** As a Data Science Researcher, I want to pass a YAML template to the CLI so that I can reuse complex plot configurations without typing out long commands.
- **Acceptance Criteria (BDD Format):**
  - **Scenario 1:** Valid YAML template
    - **Given** a valid YAML file defining a specific recipe (e.g., "Inline Defect Review")
    - **When** the CLI is executed with the template flag
    - **Then** the plot is generated applying all the rules and stylings defined in the YAML file.
- **Business Rules:** The corporate theme (Primary and Secondary hex colors) must be configurable via an external file.

### EPIC-7: Multi-Channel Categorical State Gantt
**Description:** Provide a `dp gantt` subcommand that renders longitudinal categorical state timelines across multiple independent channels (entities) in vertically-stacked, time-aligned panels. The chart automatically aggregates high-density data to prevent visual aliasing, supports global event overlays, allows domain-specific color palettes, and displays per-channel summary statistics — all while inheriting the core three-tier typography and golden-margin style system.

#### USER STORY-7.1: Faceted Multi-Panel Layout with Shared X-Axis
- **User Story:** As a Data Analyst, I want to plot the categorical state timelines of multiple distinct entities in vertically stacked panels sharing a single X-axis, so that I can easily spot correlations or synchronous state changes across different parts of the system.
- **Acceptance Criteria (BDD Format):**
  - **Scenario 1:** Multi-channel canvas division
    - **Given** a dataset containing temporal state data for two or more distinct entities specified via `--channel`
    - **When** the `dp gantt` command is executed
    - **Then** the canvas is divided into equal-height stacked horizontal panels — one per channel
    - **And** all panels share the exact same X-axis time scale with pixel-perfect vertical alignment.
  - **Scenario 2:** X-axis label suppression on upper panels
    - **Given** a multi-panel layout is generated
    - **When** the chart is rendered
    - **Then** only the bottom-most panel displays X-axis datetime text labels; all upper panels display tick marks only (labels hidden via `tick_params(labelbottom=False)`).
  - **Scenario 3:** Single-channel degenerate case
    - **Given** only one channel is present in the data
    - **When** the chart is rendered
    - **Then** a single panel is displayed with full X-axis labels as in any other standard plot type.
  - **Scenario 4:** Missing required column
    - **Given** the `--time` or `--state` column name does not exist in the input file
    - **When** the command is executed
    - **Then** the CLI exits with a clear error message identifying the missing column and no output file is created.
- **Business Rules:** Panel heights are equal and locked; they cannot be customized per-channel via CLI flags. All three-tier typography, golden margin, mirror tick, and Petroff palette rules from EPIC-2 apply to the entire canvas without modification.

#### USER STORY-7.2: Zero-Config High-Density Data Aggregation
- **User Story:** As a Domain Expert, I want the system to automatically aggregate highly compressed temporal data when viewing long timeframes, so that I do not lose visibility of brief but critical state occurrences.
- **Acceptance Criteria (BDD Format):**
  - **Scenario 1:** Aggregation mode activated (high-density data)
    - **Given** a data density where state spans would render narrower than a 2-pixel visual threshold on the current canvas dimensions and DPI
    - **When** the chart is generated
    - **Then** the system automatically enters "Aggregation Mode," grouping data into fixed time buckets (hourly or daily, selected automatically) and rendering proportional stacked bars showing the percentage of time spent in each state per bucket.
  - **Scenario 2:** Exact interval rendering (low-density data)
    - **Given** a timeframe where state spans are wide enough to be fully legible (rendered span width ≥ 2 pixels)
    - **When** the chart is generated
    - **Then** the system renders exact horizontal Gantt bars with precise start and end timestamps — no aggregation applied.
  - **Scenario 3:** Zero-config mode detection
    - **Given** any valid `dp gantt` dataset
    - **When** the chart is generated
    - **Then** the aggregation mode is selected entirely by internal heuristics (canvas pixel width ÷ total time span ÷ minimum state duration); no user flag is required or available to override this decision.
- **Business Rules:** The pixel-width threshold (2 px) is an internal constant in `DSPStyleContext` and is not user-configurable. Time bucket granularity (hourly or daily) is selected automatically based on the total visible time span.

#### USER STORY-7.3: Global Event Overlays
- **User Story:** As an Operations Manager, I want to overlay global system events or domain-wide milestones across all entity panels, so that I can visually assess how external factors impact the states of individual entities.
- **Acceptance Criteria (BDD Format):**
  - **Scenario 1:** Single-point event overlay
    - **Given** event data containing a single ISO-8601 timestamp provided via `--events`
    - **When** the chart is rendered
    - **Then** a dashed vertical line spans the full height of the main canvas, passing synchronously through all entity panels.
  - **Scenario 2:** Duration event overlay
    - **Given** event data containing a start and end ISO-8601 timestamp
    - **When** the chart is rendered
    - **Then** a semi-transparent shaded region spans the full height of the canvas across all panels for the defined duration.
  - **Scenario 3:** No events provided
    - **Given** the `--events` flag is omitted
    - **When** the chart is rendered
    - **Then** the chart renders normally with no overlay artifacts or layout shift.
  - **Scenario 4:** Event timestamp outside visible time range
    - **Given** an event timestamp that falls fully outside the plotted X-axis range
    - **When** the chart is rendered
    - **Then** the event overlay is silently omitted and no error is raised; a warning is printed to stdout.
- **Business Rules:** Event overlays are rendered as the topmost layer, visually above all Gantt bars and aggregation bins. Event marker colors and line styles must be visually distinct from all categorical state colors to prevent ambiguity.

#### USER STORY-7.4: Domain Color Mapping, Row-Level Statistics & Unified Legend
- **User Story:** As a System User, I want the chart to support domain-specific color mapping for categorical states, display local statistics for each entity, and produce a unified legend, so that the chart is immediately interpretable without external references.
- **Acceptance Criteria (BDD Format):**
  - **Scenario 1:** Domain-specific palette override
    - **Given** the user provides a `--domain-palette` argument (a JSON/YAML mapping of `state → hex color`)
    - **When** the chart is rendered
    - **Then** the specified colors are applied to the corresponding categorical states, overriding the default Petroff sequence.
    - **And** each provided color must maintain a grayscale luminance contrast ratio of at least 3:1 against adjacent-state colors; if this is violated, a warning is emitted and rendering continues.
  - **Scenario 2:** Default Petroff palette applied when no domain palette is specified
    - **Given** no `--domain-palette` is provided
    - **When** the chart is rendered
    - **Then** the default Petroff palette is assigned to categorical states in order of first appearance in the data.
  - **Scenario 3:** Row-level summary statistics
    - **Given** the multi-panel layout is generated
    - **When** the chart is finalized
    - **Then** each panel automatically computes and displays its own summary metrics (state distribution percentages and total N count) aligned to the right margin of its respective row.
    - **And** the statistics text fits entirely within the predefined right margin without causing the main data canvas area to shrink.
  - **Scenario 4:** Unified legend at the bottom of the canvas
    - **Given** the chart contains multiple categorical state colors and/or event overlay styles
    - **When** the chart is finalized
    - **Then** a single comprehensive legend is auto-generated at the bottom of the canvas, documenting all categorical state colors and all event line/shading styles used.
  - **Scenario 5:** Empty channel (no data in range)
    - **Given** a specified channel has no state records within the plotted time range
    - **When** the chart is rendered
    - **Then** the panel is rendered as an empty row with a centered "No Data" annotation; no error is raised.
- **Business Rules:** Row-level statistics text uses 10 pt Regular weight, consistent with the stats box rule in US-2.6. Domain palette overrides are applied per-run only and must not mutate the global `DSPStyleContext`. The 3:1 grayscale contrast invariant is enforced at palette construction time with a clear warning; rendering is not blocked.

### EPIC-8: Dual-Panel State Transition Matrix
**Description:** Provide a specialized analytical heatmap that computes consecutive state-to-state transition frequencies from a chronological state log and presents both raw counts and row-normalized probabilities in a side-by-side dual-panel layout. This enables users to identify dominant transition workflows, detect anomalous state-switching loops, and assess conditional likelihood of future states at a glance.

#### USER STORY-8.1: Dual-Panel Comparative Layout (Count vs. Probability)
- **User Story:** As a Data Analyst, I want to see raw transition counts and row-normalized transition probabilities side-by-side in a single chart, so that I can evaluate both the absolute volume of a transition and its relative likelihood simultaneously.
- **Acceptance Criteria (BDD Format):**
  - **Scenario 1:** Dual-panel generation from a valid state log
    - **Given** a CSV dataset containing chronological categorical state records for one or more entities
    - **When** `dp transition` is invoked
    - **Then** the canvas is split horizontally into two equal-width panels (1:1 ratio).
    - **And** the left panel is titled "TRANSITION COUNT" and displays the raw count heatmap.
    - **And** the right panel is titled "TRANSITION PROBABILITY" and displays the row-normalized probability heatmap, where each row sums to 1.0.
    - **And** both panels share identical state category labels on both X (Next State) and Y (Current State) axes with the same sort order.
  - **Scenario 2:** Single-state dataset (degenerate case)
    - **Given** all records contain the same categorical state
    - **When** `dp transition` is invoked
    - **Then** a 1×1 matrix is rendered correctly as a self-transition with count N and probability 1.0; no error is raised.
  - **Scenario 3:** Missing required column
    - **Given** the input CSV does not contain the column specified by `--state-col`
    - **When** `dp transition` is invoked
    - **Then** the CLI exits with a non-zero code and prints an actionable error message naming the missing column.
- **Business Rules:** The dataset must be internally sorted by entity and then by timestamp before consecutive pairs are extracted, to guarantee transitions reflect temporal reality rather than row order.

#### USER STORY-8.2: Logarithmic Color Scale & Independent Panel Palettes
- **User Story:** As a Reliability Engineer, I want the count panel to use a logarithmic color scale and the two panels to use visually distinct color gradients, so that extremely rare transitions remain visible and I can instantly distinguish count data from probability data.
- **Acceptance Criteria (BDD Format):**
  - **Scenario 1:** Log normalization applied to count panel
    - **Given** transition count data spanning multiple orders of magnitude (e.g., from 1 to 1,000,000)
    - **When** the left "Count" panel is rendered
    - **Then** the color mapping applies `log(1 + count)` normalization (equivalent to `LogNorm(vmin=1)`) rather than a linear scale.
    - **And** a color bar is appended to the left panel labeled with the log scale axis.
  - **Scenario 2:** Independent palettes prevent cognitive cross-contamination
    - **Given** the dual-panel layout is rendered
    - **When** colors are applied
    - **Then** the Count panel uses a warm sequential gradient (e.g., `YlOrRd`) and the Probability panel uses a cool sequential gradient (e.g., `Blues`).
    - **And** the two gradients must be visually non-overlapping in hue to prevent ambiguity.
  - **Scenario 3:** All-zero row (state never occurs as source)
    - **Given** a state exists in the dataset as a destination but never as a source transition
    - **When** the probability panel is rendered
    - **Then** the corresponding row is filled with zero-probability values and rendered in the lowest gradient color; no division-by-zero error is raised.
- **Business Rules:** Log normalization is always applied to the count panel regardless of data range; there is no user flag to override it. The minimum count value passed to `LogNorm` is clamped to 1 to avoid `log(0)` errors.

#### USER STORY-8.3: Visual Highlighting of Self-Transitions (Diagonal Bounds)
- **User Story:** As a System Architect, I want self-transitions (where the current state and next state are identical) to be visually distinguished from cross-category transitions, so that I can separate internal state persistence from meaningful phase changes at a glance.
- **Acceptance Criteria (BDD Format):**
  - **Scenario 1:** Diagonal cell border applied on both panels
    - **Given** the transition matrices are rendered
    - **When** the grid is finalized
    - **Then** a distinct visual border (bold solid black stroke, linewidth ≥ 2.5) is automatically drawn around every diagonal cell (where row index == column index) on **both** the Count and Probability panels.
    - **And** the border is rendered as the topmost layer, visible above the cell fill color.
  - **Scenario 2:** No diagonal cells present (all transitions are cross-state)
    - **Given** the input dataset contains no consecutive records in the same state
    - **When** the grid is rendered
    - **Then** no diagonal borders are drawn and no error is raised; the diagonal cells render as ordinary zero-count / zero-probability cells.
- **Business Rules:** The diagonal border is a fixed visual element controlled by `DSPStyleContext`; its linewidth and color are not user-configurable.

#### USER STORY-8.4: In-Cell Data Annotations & Axis Readability
- **User Story:** As a Report Reader, I want to read the exact numerical value inside each heatmap cell and clearly read all state names on the axes, so that I can extract precise figures without referencing the color bar and without tilting my head to read labels.
- **Acceptance Criteria (BDD Format):**
  - **Scenario 1:** In-cell annotation with adaptive text color
    - **Given** the heatmap grids are rendered
    - **Then** the exact numerical value is printed in the center of every cell.
    - **And** Count values are formatted as comma-separated integers (e.g., `210,350`).
    - **And** Probability values are formatted as two-decimal floats (e.g., `0.96`).
    - **And** the annotation text color (black `#000000` or white `#FFFFFF`) is automatically selected based on the WCAG 2.1 relative luminance of the cell's background color: white text on dark backgrounds (luminance < 0.179), black text on light backgrounds (luminance ≥ 0.179).
  - **Scenario 2:** X-axis label auto-rotation for long state names
    - **Given** one or more categorical state names on the X-axis exceed the standard bounding box (e.g., names longer than 8 characters or more than 6 states present)
    - **When** the chart is rendered
    - **Then** all X-axis tick labels are automatically rotated to 45 degrees with right-aligned horizontal alignment to prevent text overlap.
  - **Scenario 3:** Zero-count cell annotation
    - **Given** a transition pair has never been observed (count = 0)
    - **When** the chart is rendered
    - **Then** the cell is annotated with `"0"` (count panel) and `"0.00"` (probability panel) in an appropriate contrast color.
- **Business Rules:** In-cell annotations are always rendered; there is no user flag to suppress them. Luminance inversion uses the WCAG 2.1 relative luminance formula (identical to that used by `validate_grayscale_contrast()` in `metrics.py`), ensuring consistency across the codebase.

## 3. Non-Functional Requirements (NFRs)
These define how the system must behave, beyond its specific features.

- **Usability:** The CLI must provide excellent, auto-generated help menus (`--help`) outlining all available commands and flags clearly, leveraging the `Typer` framework.
- **Performance:** Ingesting and processing large Fab CSV/Parquet files must be rapid and memory-efficient, leveraging the `Polars` data engine. Generating a plot should ideally take less than a few seconds.
- **Maintainability:** The codebase must follow standard Python best practices (e.g., PEP 8 style, strict typing) to allow for easy extensibility by internal data science teams.
- **Output Quality:** The visualization engine (`Matplotlib` + `Proplot`) must strictly output in vector formats to guarantee statistical legibility and "Scientific Authority."
- **Style Integrity:** All `DSPStyleContext` styling constants (golden margins, three-tier font ratios, Petroff palette, mirror-tick settings) must be immutable at runtime. Any modification to these defaults requires a versioned release and a changelog entry.
- **Accessibility:** The Petroff palette must ensure a minimum luminance contrast ratio of 3:1 between adjacent data series in grayscale, supporting legibility for colorblind users (deuteranopia, protanopia) and monochrome print.

## 4. Glossary & Definitions
- **Fab:** Semiconductor fabrication plant.
- **Yield Enhancement:** The process of identifying and reducing defects to increase the percentage of functional chips on a wafer.
- **Process Integration:** The engineering discipline focused on making different semiconductor manufacturing steps work together.
- **CERN Style:** A rigorous, highly structured style of data visualization common in particle physics, prioritizing statistical clarity, metadata, and scientific authority over decorative aesthetics.
- **Cpk:** Process Capability Index, a statistical measure of a process's ability to produce output within specification limits.
- **UCL / LCL:** Upper Control Limit / Lower Control Limit, used in statistical process control.
- **Three-Tier Typography:** The visual text hierarchy enforced on every DSPrinter canvas: Tier-1 (Bold brand/project tag, top-left), Tier-2 (Italic status tag at 0.75–0.80x, adjacent to Tier-1), Tier-3 (Regular context info at 0.60x, top-right outside frame).
- **Golden Margin:** The locked canvas margin ratios (L: 15%, B: 12%, T: 8–10%, R: 5%) derived from high-energy physics visualization standards to guarantee visual breathing room across all plot types.
- **Mirror Ticks:** Tick marks rendered on all four sides of a plot frame, pointing inward toward the data area, enabling precise value alignment from any edge of the chart.
- **Petroff Palette:** A colorblind-accessible, grayscale-distinguishable color set based on Petroff principles, using dark blue, orange, dark red, and gray as primary colors. Replaces high-saturation software defaults.
- **Composite Chart (7:3 Split):** A two-panel layout where the main data panel occupies 70% of the canvas height and a ratio/residual panel occupies the lower 30%, with a shared, pixel-aligned X-axis.
- **Residual / Ratio Panel:** The lower panel in a composite chart displaying derived metrics such as `Data / Prediction`, `Residuals [σ]`, or period-over-period change rate.
- **Channel:** A named, independent entity (e.g., a server, a CI/CD pipeline stage, a department) whose categorical state is tracked over time in a Gantt chart. Each channel occupies one dedicated panel in the faceted layout.
- **Aggregation Mode:** A zero-config rendering mode automatically activated when data density exceeds the visual pixel threshold. Replaces exact Gantt bars with proportional stacked bins representing the fraction of time spent in each categorical state per time bucket.
- **Gantt Bar:** A horizontal bar spanning a precise start-to-end time interval, representing the duration of a single categorical state for one channel in exact-interval rendering mode.
- **Domain-Specific Palette:** A user-supplied color mapping (`state → hex`) that overrides the default Petroff palette for specific categorical states, subject to grayscale contrast validation (minimum 3:1 luminance ratio between adjacent states).
- **Proportional Stacked Bar:** A rendering unit used in Aggregation Mode. Each bar represents one time bucket and is divided into colored segments whose widths are proportional to the percentage of time spent in each categorical state during that bucket.
- **EventOverlay:** A global annotation rendered across all Gantt panels simultaneously — a dashed vertical line for point-in-time events or a semi-transparent shaded band for duration events — used to contextualize state data against external milestones or system-wide triggers.
- **Transition Matrix:** A square N×N matrix where cell [i, j] records the count (or probability) of a consecutive state change from state i (current) to state j (next), derived by scanning sorted chronological state records and counting adjacent-pair occurrences.
- **Row-Normalized Probability:** The conditional probability P(next = j | current = i), computed by dividing each cell in a count row by that row's total count. Each row in the resulting probability matrix sums to exactly 1.0 (or 0.0 for states that never appear as a source).
- **Self-Transition:** A consecutive state record pair where the current and next state labels are identical (i == j); occupies the main diagonal of the transition matrix and typically represents state persistence rather than a phase change.
- **Log Scale Colormap:** A color mapping applied to the Count panel that normalizes cell values using log(1 + count) (via LogNorm(vmin=1)), ensuring that transitions spanning multiple orders of magnitude remain individually visible.
- **Dual-Panel Heatmap:** The 1:1 horizontally split canvas pattern used by dp transition, where the left panel renders count data with a warm gradient and the right panel renders probability data with a cool gradient.
- **Cell Luminance Inversion:** An automatic contrast mechanism that selects black (#000000) or white (#FFFFFF) for in-cell annotation text based on the WCAG 2.1 relative luminance of the cell background fill color, using threshold 0.179.
