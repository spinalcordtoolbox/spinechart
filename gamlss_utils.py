from pathlib import Path
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri, default_converter
from rpy2.robjects.conversion import localconverter

MODEL_PATH = Path("output/models/csa_bct.rds")


def save_model(fit):
    ro.globalenv["fit"] = fit
    ro.r(f'saveRDS(fit, "{MODEL_PATH.as_posix()}")')

def load_model():
    fit = ro.r(f'readRDS("{MODEL_PATH.as_posix()}")')
    return fit

def pandas_to_r(df):
    with localconverter(default_converter + pandas2ri.converter):
        r_df = pandas2ri.py2rpy(df)
    return ro.r("as.data.frame")(r_df)