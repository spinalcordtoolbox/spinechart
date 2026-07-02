"""
gamlss_predict.py
------------------
Site-neutral BCT distributional parameters without calling predict.gamlss.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import rpy2.robjects as ro
from gamlss_utils import _ensure_helpers

# Fixing windows environment path variables
import os
os.add_dll_directory(r"C:\Program Files\R\R-4.6.0\bin\x64")
os.environ["R_HOME"] = r"C:\Program Files\R\R-4.6.0"
os.environ["PATH"]   = r"C:\Program Files\R\R-4.6.0\bin\x64;" + os.environ["PATH"]


def build_prediction_df(r_fit, grid: pd.DataFrame) -> pd.DataFrame:
    """
    Compute site-neutral BCT parameters for every row in grid.
    grid must contain columns: age, slice_idx, sex_bin.
    """
    _ensure_helpers()

    missing = {"age", "slice_idx", "sex_bin"} - set(grid.columns)
    if missing:
        raise ValueError(f"grid is missing columns: {missing}")

    ro.globalenv["r_fit"] = r_fit

    r_params = ro.r["predict_gamlss_params"](
        r_fit,
        ro.FloatVector(grid["age"].astype(float).tolist()),
        ro.FloatVector(grid["slice_idx"].astype(float).tolist()),
        ro.FloatVector(grid["sex_bin"].astype(float).tolist()),
        True,  # site_neutral
    )

    out = grid.reset_index(drop=True).copy()
    for col in list(r_params.names):
        out[col] = np.asarray(r_params.rx2(col))
    for col in ("mu", "sigma", "nu", "tau"):
        if col not in out.columns:
            out[col] = np.nan
    return out


def validate_bypass(r_fit, n_sample: int = 500) -> bool:
    """
    Validate predictions against stored fit$mu.lp
    Returns True if corr > 0.999 and MAE < 0.01.
    """
    _ensure_helpers()
    ro.globalenv["r_fit"] = r_fit

    # Pull training data from R
    train_df = pd.DataFrame({
        "age":       np.asarray(ro.r("as.numeric(r_fit$data$age)")),
        "slice_idx": np.asarray(ro.r("as.numeric(r_fit$data$slice_idx)")),
        "sex_bin":   np.asarray(ro.r("as.numeric(r_fit$data$sex_bin)")),
    })

    idx    = train_df.sample(n=min(n_sample, len(train_df)), random_state=42).index
    sample = train_df.loc[idx].reset_index(drop=True)

    # Bypass prediction
    preds = build_prediction_df(r_fit, sample)

    # Response-scale check (MAE expected > 0 due to site offsets)
    mu_fv  = np.asarray(ro.r("as.numeric(r_fit$mu.fv)"))[idx]
    corr_r = np.corrcoef(preds["mu"].values, mu_fv)[0, 1]
    mae_r  = np.mean(np.abs(preds["mu"].values - mu_fv))
    print(f"Response scale  — corr(bypass, mu.fv)        = {corr_r:.4f},  MAE = {mae_r:.4f}")
    print("  (MAE > 0 expected: site BLUPs removed in bypass)")

    # Link-scale check: compare log(bypass_mu) vs mu.lp - random column
    ro.r("""
    .rand_col      <- grep("random", colnames(r_fit$mu.s), ignore.case=TRUE)
    .mu_lp_det     <- as.numeric(r_fit$mu.lp - r_fit$mu.s[, .rand_col])
    """)
    mu_lp_det = np.asarray(ro.r("as.numeric(.mu_lp_det)"))[idx]
    bypass_eta = np.log(np.maximum(preds["mu"].values, 1e-12))  # log since mu.link = "log"

    corr_l = np.corrcoef(bypass_eta, mu_lp_det)[0, 1]
    mae_l  = np.mean(np.abs(bypass_eta - mu_lp_det))
    print(f"Link scale (det) — corr(log(bypass), lp_det) = {corr_l:.4f},  MAE = {mae_l:.6f}")
    print("  (target: corr > 0.999, MAE < 0.01)")

    # Range check
    ro.r("""
    cat("mu.lp_det range     :", range(.mu_lp_det), "\n")
    cat("exp(range) = mu range:", exp(range(.mu_lp_det)), "\n")
    cat("slice_idx range     :", range(r_fit$data$slice_idx), "\n")
    """)

    return bool(corr_l > 0.999 and mae_l < 0.01)


def save_predictions(params: pd.DataFrame,
                     path: str = "output/predictions/params.parquet") -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    params.to_parquet(p, index=False)
    print(f"Saved {len(params):,} rows → {p}")