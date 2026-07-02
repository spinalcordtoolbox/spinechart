from pathlib import Path
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri, default_converter
from rpy2.robjects.conversion import localconverter


_HELPERS_PATH = Path(__file__).parent / "gamlss_helper.R"
_helpers_sourced = False


def _ensure_helpers():
    """Source gamlss_helpers.R once per process."""
    global _helpers_sourced
    if not _helpers_sourced:
        ro.r(f'source("{_HELPERS_PATH.as_posix()}")')
        _helpers_sourced = True

def load_model(rds_path):
    return ro.r(f'readRDS("{Path(rds_path).as_posix()}")')

def pandas_to_r(df):
    with localconverter(default_converter + pandas2ri.converter):
        r_df = pandas2ri.py2rpy(df)
    return ro.r("as.data.frame")(r_df)