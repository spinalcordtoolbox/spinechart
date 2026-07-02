"""
build_grid.py
-------------
Build the (age × slice_idx × sex_bin) prediction grid and save it.
The grid is metric-agnostic; one file serves all models.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from parsing import run_parsing_pipeline


def build_grid(
    age_range:       tuple = None,
    age_step:        float = 1.0,
    slice_idx_range: tuple = None,   # inferred from data if None
    sex_values:      list  = [0, 1],
    out_path:        str   = "output/predictions/grid.parquet",
) -> pd.DataFrame:
    """
    Build a dense prediction grid.

    If age_range/slice_idx_range is None, it is inferred from the training data so the
    grid exactly covers the observed range.
    """
    if age_range is None:
        raw_df, _ = run_parsing_pipeline()
        a_min = int(raw_df["age"].min())
        a_max = int(raw_df["age"].max())
        print(f"Inferred age range from data: [{a_min}, {a_max}]")
    else:
        a_min, a_max = age_range
    
    if slice_idx_range is None:
        raw_df, _ = run_parsing_pipeline()
        raw_df = raw_df.rename(columns={"Slice (I->S)": "slice_idx"})
        s_min = int(raw_df["slice_idx"].min())
        s_max = int(raw_df["slice_idx"].max())
        print(f"Inferred slice_idx range from data: [{s_min}, {s_max}]")
    else:
        s_min, s_max = slice_idx_range

    ages = np.arange(a_min, a_max + age_step, age_step)
    slices = np.arange(s_min, s_max + 1, 1)
    sex_arr = np.array(sex_values)

    grid = pd.DataFrame(
        [(a, s, x)
         for a in ages
         for s in slices
         for x in sex_arr],
        columns=["age", "slice_idx", "sex_bin"],
    )

    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    grid.to_parquet(p, index=False)
    print(f"Grid: {len(grid):,} rows → {p}")
    return grid


if __name__ == "__main__":
    build_grid()