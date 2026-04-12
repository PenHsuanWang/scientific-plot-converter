# Software Design Document (SDD): FabPlot-CLI

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
- **Aggregates & Entities:**
  - `PlotJob`: The main aggregate root representing a single CLI execution, containing the dataset references, plot parameters, and final output destinations.
  - `FabStyleContext`: Entity ensuring the locking of typography, color-blind palettes, and "Scientific Style" rules.

## 4. Component Design (LLD)
- **Microservices / Modules:**
  - `fabplot.cli`: Typer application entry points (e.g., `@app.command() def hist1d(...)`).
  - `fabplot.data.io`: Polars wrappers to load and validate CSV/Parquet.
  - `fabplot.stats.metrics`: Core functions calculating $N$, $\mu$, $\sigma$, $C_{pk}$, and smart binning rules.
  - `fabplot.render.engine`: Abstraction layer over Matplotlib/Proplot. Contains builder classes for creating the "CERN Layout" (Top-Left Status, Top-Right Header, Margin Data Tables).
  - `fabplot.render.plots`: Specific implementation classes (`HistogramPlotter`, `TrendPlotter`).
- **Design Patterns:**
  - **Strategy Pattern:** For determining the plot type (`hist1d` vs `trend`).
  - **Builder Pattern:** To construct the complex figure layout step-by-step (Base Canvas -> Axes -> Data Lines -> Statistical Annotations -> Metadata Headers).

## 5. Data Design
- **Logical Schema:**
  - The system operates on in-memory column-oriented data structures (`polars.DataFrame`). No persistent internal schema.
- **Storage Solutions:**
  - Ephemeral memory during execution. Output is committed to the local filesystem as `.pdf` or `.svg`.
- **Data Flow:**
  1. User invokes `fabplot hist1d --input data.csv`.
  2. `typer` parses arguments and instantiates `PlotJob`.
  3. `polars` lazily loads `data.csv` (or eagerly if filtering is required).
  4. Statistics are computed on the requested `--x` column.
  5. The `render.engine` initializes the canvas with the `FabStyleContext`.
  6. `render.plots` maps the data and statistics to the canvas.
  7. The figure is saved to the output path.

## 6. UI & Interaction Design
- **Key User Journeys:**
  - **Discovery:** User runs `fabplot --help` and receives a rich, organized terminal UI describing plot types and flags.
  - **Generation:** User runs a declarative command `fabplot trend --x time --y CD --norm --style internal_confidential`. The CLI provides a brief progress indicator and outputs the file path of the generated PDF.
- **State Management:** The application is entirely stateless between executions.

## 7. Technical Specifications & Non-Functional Requirements
- **Performance:** `polars` guarantees fast I/O and processing, capable of handling gigabytes of metrology data efficiently. Plot rendering should complete within seconds.
- **Reliability:** "Zero-Config Styling" prevents the user from breaking the layout. The tool must gracefully handle and log errors for missing columns or mathematically invalid data (e.g., calculating $C_{pk}$ on zero variance) without crashing abruptly.
- **Visual Accuracy:** "Vector First" requirement mandates that all geometric primitives (lines, hatches, fonts) are infinitely scalable. Aliasing and pixelation are strictly prohibited for production outputs.
