"""
gamlss_align.py
-----------------
Aligning out-of-sample studies using functions from gamlss_helper.R
"""
from gamlss_utils import _ensure_helpers
from r_setup import configure_r_environment
configure_r_environment()
import rpy2.robjects as ro



def align_cohort_by_cn(r_fit, df,
                        dataset_col="dataset_name", subject_col="participant_id",
                        diagnosis_col="pathology", value_col="value",
                        age_col="age", slice_col="slice_idx", sex_col="sex_bin",
                        cn_label="HC", min_cn_for_alignment=10, site_neutral=True):
    """Align an external cohort to the normative GAMLSS reference chart

    Args:
        r_fit (gamlss.fit object): fitted gamlss model
        df (pd.DataFrame): df containing the columns described bellow
        dataset_col (str, optional): column containing the dataset name. Defaults to "dataset_name".
        subject_col (str, optional): column containing subjects ids. Defaults to "participant_id".
        diagnosis_col (str, optional): column containing the subject's diagnosis. Defaults to "pathology".
        value_col (str, optional): column containing the metric value. Defaults to "value".
        age_col (str, optional): column containing subject's age. Defaults to "age".
        slice_col (str, optional): column containing slices. Defaults to "slice_idx".
        sex_col (str, optional): column containing subject's sex. Defaults to "sex_bin".
        cn_label (str, optional): label used for healthy patients. Defaults to "HC".
        min_cn_for_alignment (int, optional): minimum number of healthy subjects for alignement. Defaults to 10.
        site_neutral (bool, optional): Defaults to True.

    Raises:
        ValueError: error if columns are missing

    Returns:
        dict: contains aligned data, estimated site corrections, summary
    """
    _ensure_helpers()
    required = {age_col, slice_col, sex_col, value_col, dataset_col, subject_col, diagnosis_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Cohort data is missing columns: {missing}")

    from rpy2.robjects import pandas2ri
    from rpy2.robjects.conversion import localconverter

    ro.globalenv["r_fit"] = r_fit
    ro.globalenv["fit"] = r_fit

    with localconverter(ro.default_converter + pandas2ri.converter):
        r_df = ro.conversion.py2rpy(df)

    r_result = ro.r["align_to_reference_chart_by_cn"](
        data=r_df,
        fit=r_fit,
        value_col=value_col,
        dataset_col=dataset_col,
        subject_col=subject_col,
        diagnosis_col=diagnosis_col,
        age_col=age_col,
        slice_col=slice_col,
        sex_col=sex_col,
        cn_label=cn_label,
        min_cn_for_alignment=min_cn_for_alignment,
        site_neutral=site_neutral,
    )
    
    with localconverter(ro.default_converter + pandas2ri.converter):
        aligned = ro.conversion.rpy2py(r_result.rx2("data"))
        parameters = ro.conversion.rpy2py(r_result.rx2("parameters"))
        summary = ro.conversion.rpy2py(r_result.rx2("summary"))

    return {
        "data": aligned,
        "parameters": parameters,
        "summary": summary,
    }