"""
gamlss_fit.py
-------------
Fit a BCT GAMLSS model for one metric. Callable per-metric or run as a script
to fit all metrics sequentially.
"""
import os
import rpy2.robjects as ro
from pathlib import Path
from parsing import run_parsing_pipeline
from gamlss_utils import pandas_to_r
from config.metrics import METRIC_MODEL_CONFIG

# Fixing windows environment paths
os.add_dll_directory(r"C:\Program Files\R\R-4.6.0\bin\x64")
os.environ["R_HOME"] = r"C:\Program Files\R\R-4.6.0"
os.environ["PATH"]   = r"C:\Program Files\R\R-4.6.0\bin\x64;" + os.environ["PATH"]


def prepare_metric_df(raw_df, metric: str):
    """Rename raw column to model_col (R compatible name) and return only the required columns."""
    cfg = METRIC_MODEL_CONFIG[metric]
    return (
        raw_df
        .rename(columns={
            cfg["raw_col"]:  cfg["model_col"],
            "Slice (I->S)":  "slice_idx",
        })
        [[cfg["model_col"], "age", "slice_idx", "sex_bin", "dataset_name"]]
        .dropna()
    )


def fit_model(df, metric):
    """
    Fit a BCT GAMLSS model for the given metric and save the RDS file.
    Args:
        df (pd.DataFrame): parsed dataframe with R compatible column names
        metric (str): R compatible metric name

    Returns:
        None
    """
    cfg = METRIC_MODEL_CONFIG[metric]
    model_col = cfg["model_col"]
    link      = cfg["link"]
    rds_path  = cfg["rds_path"]

    if model_col not in df.columns:
        raise ValueError(
            f"Column '{model_col}' not found in df for metric '{metric}'. "
            f"Available: {df.columns.tolist()}"
        )

    Path(rds_path).parent.mkdir(parents=True, exist_ok=True)

    # R global environment variables
    ro.globalenv["df"]       = pandas_to_r(df)
    ro.globalenv["response"] = ro.StrVector([model_col])
    ro.globalenv["rds_path"] = ro.StrVector([rds_path])

    # GAMLSS fitting
    ro.r("""
    library(gamlss)
    library(gamlss.add)

    formula_str <- paste0(
        response, " ~ fp(age, 2) + pb(slice_idx) + sex_bin + random(as.factor(dataset_name))"
    )
    sigma_str <- "~ fp(age, 2) + pb(slice_idx) + sex_bin + random(as.factor(dataset_name))"

    .fit <- gamlss(
        formula       = as.formula(formula_str),
        sigma.formula = as.formula(sigma_str),
        nu.formula    = ~ 1,
        tau.formula   = ~ 1,
        family        = BCT(mu.link = "log"),
        data          = df,
        control       = gamlss.control(n.cyc = 200, trace = FALSE)
    )

    .fit$data <- df
    saveRDS(.fit, rds_path)
    cat("Saved:", rds_path, "\n")
    """)



if __name__ == "__main__":
    import sys

    metrics_to_fit = sys.argv[1:] or list(METRIC_MODEL_CONFIG.keys())
    print(f"Fitting metrics: {metrics_to_fit}")

    raw_df, _ = run_parsing_pipeline()

    for metric in metrics_to_fit:
        print(f"\n{'─'*60}")
        print(f"  Fitting: {metric}")
        df = prepare_metric_df(raw_df, metric)
        print(f"  Rows: {len(df):,}")
        fit_model(df, metric)
        print("  Done.")