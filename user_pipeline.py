"""
Deals with user's data
- Load user's data
- Parse them
- Align them to the normative charts
- Return the harmonized aligned data
"""

from pathlib import Path
import argparse
import base64
import zipfile
import tempfile

from parsing import load_dataset, clean_data
from gamlss_utils import load_model
from gamlss_align import align_cohort_by_cn
from config.metrics import METRIC_MODEL_CONFIG


def save_uploaded_zip(contents, filename):
    """
    Save temporarily the Dash uploaded zip and extract it. (For GUI pipeline)

    Returns:
        Path to extracted dataset directory
    """

    _, content_string = contents.split(",")

    decoded = base64.b64decode(content_string)

    tmp_dir = Path(tempfile.mkdtemp())

    zip_path = tmp_dir / filename

    with open(zip_path, "wb") as f:
        f.write(decoded)

    extract_dir = tmp_dir / "dataset"
    extract_dir.mkdir()

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)

    return extract_dir


def prepare_user_dataset(dataset_path):
    """Load and prepare an uploaded dataset for alignment using the functions in parsing.py

    Args:
        dataset_path (str): user's dataset path
    Returns:
        clean_metrics (pd.DataFrame): Prepared metrics dataframe
        clean_dem (pd.DataFrame): Demographics dataframe
    """
    dataset_path = Path(dataset_path)

    # Load raw CSV + participants.tsv
    metrics_df, dem_df = load_dataset(dataset_path) 
    # Cleaning
    clean_metrics, clean_dem = clean_data(metrics_df, dem_df)
    
    return clean_metrics, clean_dem

def prepare_new_data_for_metric(df, metric):
    """Rename columns to R compatible names and keep only the relevant columns given the metric.

    Args:
        df (pd.DataFrame): clean df
        metric (str): metric name
    Returns:
        pd.DataFrame: Formatted
    """
    cfg = METRIC_MODEL_CONFIG[metric]
    out = (df
        .rename(columns={cfg["raw_col"]: "value"})
        .rename(columns={"Slice (I->S)": "slice_idx"})
    )
    keep_extra=("participant_id", "dataset_name", "pathology")
    keep = ["value", "age", "slice_idx", "sex_bin"] + [c for c in keep_extra if c in out.columns]
    
    return out[keep].dropna(subset=["value", "age", "slice_idx", "sex_bin"])

def align_control_cohort(clean_metrics, cn_labels=["CN", "HC"], prints=False):
    """Align a healthy-control cohort to the normative database.

    Args:
        clean_metrics (pd.DataFrame): metrics df
        cn_labels (list of str, optional): Healthy subjects labels. Defaults to ["CN", "HC"].
        prints (bool): to print messages or not

    Returns:
        dict: Alignment results for every metric.
    """
    results = {}

    for metric, cfg in METRIC_MODEL_CONFIG.items():
        if prints:
            print(f"\nAligning metric: {metric}")

        metric_df = prepare_new_data_for_metric(clean_metrics, metric)

        fit = load_model(cfg["rds_path"])

        result = align_cohort_by_cn(fit, metric_df, cn_labels=cn_labels)

        results[metric] = result

    return results
    

def save_alignment_results(results, output_dir):
    """Saves alignment results locally. (For CLI pipeline)

    Args:
        results (_type_): _description_
        output_dir (_type_): _description_
    """
    output_dir = Path(output_dir)

    for metric, result in results.items():

        metric_dir = output_dir / metric
        metric_dir.mkdir(exist_ok=True, parents=True)

        result["data"].to_csv(metric_dir / "aligned_data.csv", index=False)
        result["parameters"].to_csv(metric_dir / "parameters.csv", index=False)
        result["summary"].to_csv(metric_dir / "summary.csv", index=False)

def process_user_dataset(dataset_path, output_dir="output/alignment", cn_labels=["CN", "HC"]):
    """
    Complete user pipeline for CLI.
    """

    print("Preparing user dataset...")
    clean_metrics, clean_dem = prepare_user_dataset(dataset_path)

    print("Running alignment...")
    results = align_control_cohort(clean_metrics, cn_labels=cn_labels, prints=True)

    if output_dir is not None:
        print("Saving results...")
        save_alignment_results(results, output_dir)

    return {
        "metrics": clean_metrics,
        "demographics": clean_dem,
        "alignment": results,
    }
    

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Align a user's dataset to normative charts")

    parser.add_argument(
        "dataset",
        type=str,
        help="Path to the user's dataset directory"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="output/alignment",
        help="Directory where alignment results are saved"
    )
    
    args = parser.parse_args()

    results = process_user_dataset(dataset_path=args.dataset, output_dir=args.output_dir)

    print("Done.")