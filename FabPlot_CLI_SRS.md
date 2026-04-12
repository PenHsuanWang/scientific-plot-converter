# Software Requirements Specification (SRS): FabPlot-CLI

## 1. Product Overview
- **Product Name:** FabPlot-CLI
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

## 4. Glossary & Definitions
- **Fab:** Semiconductor fabrication plant.
- **Yield Enhancement:** The process of identifying and reducing defects to increase the percentage of functional chips on a wafer.
- **Process Integration:** The engineering discipline focused on making different semiconductor manufacturing steps work together.
- **CERN Style:** A rigorous, highly structured style of data visualization common in particle physics, prioritizing statistical clarity, metadata, and scientific authority over decorative aesthetics.
- **Cpk:** Process Capability Index, a statistical measure of a process's ability to produce output within specification limits.
- **UCL / LCL:** Upper Control Limit / Lower Control Limit, used in statistical process control.
