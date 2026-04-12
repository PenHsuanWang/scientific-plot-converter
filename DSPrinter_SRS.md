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
