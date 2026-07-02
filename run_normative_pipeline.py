"""
run_normative_pipeline.py
--------------------------
Run after gamlss_fit.py and build_grid.py have completed.
For each metric:
  1. Load the fitted RDS model
  2. Run prediction over the grid and saves to params_{metric}.parquet
  3. Add centile curves and saves to centile_curves_{metric}.parquet
"""

import sys
import pandas as pd
from pathlib import Path

from config.metrics import METRIC_MODEL_CONFIG
from gamlss_predict import build_prediction_df, save_predictions
from gamlss_centiles import add_centiles_to_params, save_centile_curves, DEFAULT_CENTILES
from gamlss_utils import load_model, _ensure_helpers

import os
os.add_dll_directory(r"C:\Program Files\R\R-4.6.0\bin\x64")
os.environ["R_HOME"] = r"C:\Program Files\R\R-4.6.0"
os.environ["PATH"]   = r"C:\Program Files\R\R-4.6.0\bin\x64;" + os.environ["PATH"]


def run_pipeline_for_metric(metric, grid):
    cfg      = METRIC_MODEL_CONFIG[metric]
    rds_path = cfg["rds_path"]

    if not Path(rds_path).exists():
        print(f"  [SKIP] RDS not found: {rds_path}")
        return

    params_path  = f"output/predictions/params_{metric}.parquet"
    centile_path = f"output/predictions/centile_curves_{metric}.parquet"

    print(f"  Loading model from {rds_path} ...")
    fit = load_model(rds_path)

    _ensure_helpers()

    print(f"  Predicting params over {len(grid):,}-row grid ...")
    params = build_prediction_df(fit, grid)
    save_predictions(params, path=params_path)

    print("  Adding centile curves ...")
    curves = add_centiles_to_params(params, centiles=DEFAULT_CENTILES)
    save_centile_curves(curves, path=centile_path)

    print(f"  mu range: [{params['mu'].min():.2f}, {params['mu'].max():.2f}]")
    print(f"  Done → {centile_path}")


if __name__ == "__main__":
    metrics_to_run = sys.argv[1:] or list(METRIC_MODEL_CONFIG.keys())
    print(f"Running normative pipeline for: {metrics_to_run}\n")

    grid = pd.read_parquet("output/predictions/grid.parquet")
    print(f"Grid loaded: {len(grid):,} rows\n")

    for metric in metrics_to_run:
        print(f"{'─'*60}")
        print(f"  Metric: {metric}")
        run_pipeline_for_metric(metric, grid)