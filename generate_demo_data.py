"""Generate demo CSV data for dsprinter examples."""
import numpy as np
import polars as pl

# Set seed for reproducibility
np.random.seed(42)
N = 200

# Generate Data for Tool A (e.g., Mean 10.0, Sigma 0.5)
tool_a_data = np.random.normal(loc=10.0, scale=0.5, size=N)

# Generate Data for Tool B (e.g., Mean 10.8, Sigma 0.6) - overlapping range
tool_b_data = np.random.normal(loc=10.8, scale=0.6, size=N)

# Create a DataFrame and save to CSV
df = pl.DataFrame({
    "Tool_A_CD": tool_a_data,
    "Tool_B_CD": tool_b_data,
})

df.write_csv("demo_histogram_data.csv")
print("Generated 'demo_histogram_data.csv' with N=200 for two distributions.")
