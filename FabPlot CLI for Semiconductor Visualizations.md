This is a strategic move. In semiconductor manufacturing—especially in **Yield Enhancement** and **Process Integration**—the "CERN style" provides a level of statistical authority that standard business BI tools (like PowerBI or generic Tableau) often lack.

By adopting this, your team moves from "looking at charts" to "performing visual metrology." Here is a refined **Product Requirements Document (PRD)** outline tailored for your Product Manager, stripping away the physics jargon and replacing it with semiconductor manufacturing (Fab) equivalents.

## ---

**Project: FabPlot-CLI**

**Objective:** A standardized Python CLI utility to generate publication-quality, "Scientific-Grade" visualizations from Fab CSV data, enforcing a uniform corporate/research style for internal reports and external whitepapers.

### **1\. The "Scientific Style" Definition (Industrial Context)**

Instead of "CMS Preliminary," we focus on **Process Integrity** and **Statistical Legibility**:

* **Vector First:** All outputs default to .pdf or .svg to ensure zero pixelation in high-stakes quarterly reviews.
* **The "Fab-Header":** A standardized metadata block at the top-right (e.g., Technology Node, Layer, Tool ID, Date).
* **High Contrast/Accessible Palettes:** Using textures (hatching) and color-blind friendly palettes instead of the default "rainbow" scales.
* **Statistical Indicators:** Mandatory display of sample size ($N$), Mean ($\\mu$), and Sigma ($\\sigma$) or $C\_{pk}$ directly on the canvas in a non-obtrusive "Legend Box."

### ---

**2\. User Perspective & Usage Requirements**

The tool must follow a **Declarative Approach**: The user defines the "What," and the CLI enforces the "How."

#### **A. Core Input/Output**

* **Input:** Multi-column CSV/Parquet files (e.g., Metrology data, WAT/CP test results).
* **Command Structure:** fabplot \[PLOT\_TYPE\] \--input \[FILE\] \[MAPPING\_FLAGS\] \[STYLE\_FLAGS\]

#### **B. Plot Types (Phase 1\)**

* **hist1d (Distribution Analysis):**
  * **Requirement:** Specify \--x \[column\].
  * **Scientific Feature:** Automatic "Step" histograms (lines only) or "Filled" histograms with high-quality hatching (e.g., for comparing 'Golden Wafer' vs. 'Current Lot').
* **trend (Time-Series/Lot-Series):**
  * **Requirement:** Specify \--x \[time/lot\] and \--y \[metric\].
  * **Scientific Feature:** Inclusion of "Control Limits" (UCL/LCL) rendered as subtle shaded regions rather than distracting bright red lines.

#### **C. Texture & Annotation Logic (The "CERN" Layout)**

* **Top-Left Annotation:** Reserved for "Confidentiality" or "Status" (e.g., *INTERNAL ONLY*, *DRAFT*, *FINAL QUAL*).
* **Top-Right Annotation:** Reserved for Technical Metadata (e.g., $28nm$ HKMG, Slot 01-25).
* **The "Bottom/Side Margin" Requirement:** A dedicated flag to toggle a "Data Table" or "Parameter Summary" on the bottom axis, similar to the event-type breakdown in physics plots.

### ---

**3\. Functional Requirements for Data Science Researchers**

To ensure researchers actually use it instead of fighting with Matplotlib, the tool must provide:

| Feature | Requirement Description |
| :---- | :---- |
| **Zero-Config Styling** | No manual plt.fontsize() calls. Font sizes for axes, legends, and titles are globally locked to 10pt/12pt Arial/Helvetica. |
| **Smart Binning** | For histograms, the tool must calculate bin widths based on the data range to avoid "aliasing" or gaps in semiconductor distributions. |
| **Normalization** | A flag \--norm to switch between "Raw Count" and "Yield Density" (Probability Density Function). |
| **Multi-Overlay** | The ability to overlay multiple CSV files with a single command to compare "Chamber A" vs "Chamber B" using distinct textures. |

### ---

**4\. Technical Stack (Proposed)**

* **Environment:** Python 3.12+ (managed via **uv**).
* **CLI Framework:** Typer (for excellent auto-generated help menus).
* **Engine:** Matplotlib \+ Proplot (Proplot simplifies the scientific alignment of subplots).
* **Data Engine:** Polars (for high-speed ingestion of large Fab data files).

### ---

**Next Steps for the Product Manager:**

1. **Define the "Corporate Theme":** Finalize the hex codes for the "Primary" and "Secondary" fab colors.
2. **Schema Validation:** Define how the CLI should handle missing data (e.g., skip or interpolate).
3. **Template Library:** Create a set of YAML "recipes" for common tasks like "Inline Defect Review" or "Critical Dimension Distribution."

Does this framing align with the "Scientific Authority" you want to bring to your semiconductor analysis?
