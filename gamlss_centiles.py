"""
gamlss_centiles.py
-------------------
Build centile-values.
For each row of the prediction grid (defined age, slice_idx, sex_bin),
returns the response value corresponding to each requested centile, via the qBCT R function.
"""
from pathlib import Path

import numpy as np
import rpy2.robjects as ro
from rpy2.robjects.packages import importr

# gamlss.dist provides pBCT / qBCT
_gamlss_dist = importr("gamlss.dist")

DEFAULT_CENTILES = [5, 10, 25, 50, 75, 90, 95]


def add_centiles_to_params(params, centiles = DEFAULT_CENTILES):
    """
    Add response-scale centile columns to a DataFrame that already has mu/sigma/nu/tau

    Args:
        params (DataFrame): DataFrame containing the distribution parameters (mu/sigma/nu/tau)
        centiles (sequence of float): Percentiles in (0, 100), e.g. [5, 25, 50, 75, 95]. Defaults to DEFAULT_CENTILES.
        family (str, optional): distribution. Defaults to "BCT".
        
    Returns:
        params with one new column per centile, named "centile_{p}", holding
        the response-scale value (e.g. CSA in mm^2) at that centile.
    """

    required = {"mu", "sigma", "nu", "tau"}
    missing = required - set(params.columns)
    if missing:
        raise ValueError(f"params is missing columns: {missing}")

    mu    = ro.FloatVector(params["mu"].astype(float).tolist())
    sigma = ro.FloatVector(params["sigma"].astype(float).tolist())
    nu    = ro.FloatVector(params["nu"].astype(float).tolist())
    tau   = ro.FloatVector(params["tau"].astype(float).tolist())

    qBCT = _gamlss_dist.qBCT
    out = params.copy()

    for p in centiles:
        prob = p / 100.0
        q = qBCT(prob, mu=mu, sigma=sigma, nu=nu, tau=tau)
        out[f"centile_{p}"] = np.asarray(q)

    return out


def save_centile_curves(curves, path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    curves.to_parquet(p, index=False)
    print(f"Saved {len(curves):,} rows → {p}")