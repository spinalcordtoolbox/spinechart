"""
Deals with user's data
- Load user's data
- Parse them
- Align them to the normative charts
- Return the harmonized aligned data
"""

from pathlib import Path
import argparse

from parsing import load_dataset, clean_data
from gamlss_utils import load_model
from gamlss_align import align_cohort_by_cn
from config.metrics import METRIC_MODEL_CONFIG


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


def process_user_dataset(dataset_path, output_dir="output/alignment", cn_label="CN"):
    """Align the user's data to the normative database, and save the result in csv files

    Args:
        dataset_path (str): path to user's data
        output_dir (str, optional): path where to save the alignment results. Defaults to "output/alignment".
        cn_label (str, optional): healthy patients' label in the user's dataset. Defaults to "CN".

    Returns:
        (dict): dictionary containing the cleaned metrics df, cleaned metadata df, alignement results
    """

    output_dir = Path(output_dir)

    print("Preparing user dataset...")
    clean_metrics, clean_dem = prepare_user_dataset(dataset_path)

    print("Running alignment...")
    results = {}

    for metric, cfg in METRIC_MODEL_CONFIG.items():

        print(f"\nAligning metric: {metric}")

        metric_df = prepare_new_data_for_metric(clean_metrics, metric)

        fit = load_model(cfg["rds_path"])

        result = align_cohort_by_cn(fit, metric_df, cn_label=cn_label)

        results[metric] = result

        metric_dir = output_dir / metric
        metric_dir.mkdir(exist_ok=True, parents=True)

        result["data"].to_csv(metric_dir / "aligned_data.csv", index=False)
        result["parameters"].to_csv(metric_dir / "parameters.csv", index=False)
        result["summary"].to_csv(metric_dir / "summary.csv", index=False)

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

    parser.add_argument(
        "--cn-label",
        type=str,
        default="CN",
        help="Label used for healthy controls in pathology column (default: CN)"
    )
    
    args = parser.parse_args()

    results = process_user_dataset(dataset_path=args.dataset, output_dir=args.output_dir, cn_label=args.cn_label)

    print("\nDone.")