"""
This script handles the data parsing pipeline
It:
- Automatically finds dataset folders containing CSV files and metadata (participants.tsv)
- Loads and merges all dataset files into a single dataframe
- Cleans the combined dataset
- Outputs a dataframe ready to be used in the normative model pipeline
"""

import pandas as pd
from pathlib import Path
import subprocess


REPO_URL = "https://github.com/spinalcordtoolbox/PAM50-normalized-metrics.git"

DATA_ROOT = Path("data/PAM50-normalized-metrics")


def fetch_normative_database(repo_url=REPO_URL, local_path=DATA_ROOT):
    """
    Downloads the normative database if it does not exist.
    Otherwise updates it using git pull.

    Returns
    -------
    Path
        Local path to the repository
    """

    local_path.parent.mkdir(parents=True, exist_ok=True)

    if not local_path.exists():
        print(f"Cloning repository into: {local_path}")

        subprocess.run(
            ["git", "clone", repo_url, str(local_path)],
            check=True,
        )

    else:
        print(f"Updating repository in: {local_path}")

        subprocess.run(
            ["git", "-C", str(local_path), "pull"],
            check=True,
        )

    return local_path



def find_datasets(root):
    """
    Finds dataset folders containing CSV + participants.tsv
    (Currently only )
    """
    candidate_dir = [
        root / "spinal_cord" / "spine-generic_multi-subject",
        root / "spinal_cord" / "whole-spine",
    ]
    
    valid_datasets = []
    
    for dataset_dir in candidate_dir:
        if not dataset_dir.exists():
            raise ValueError(f"Dataset folder not found: {dataset_dir}")

        required_files = [
            dataset_dir / "participants.tsv",
            dataset_dir / "dataset_description.json",
        ]

        has_required = all(f.exists() for f in required_files)
        has_csv = any(dataset_dir.glob("*.csv"))
        
        if has_required and has_csv:
            valid_datasets.append(dataset_dir)
        else:
            raise ValueError(f"Invalid dataset structure in: {dataset_dir}")

    return valid_datasets



def load_dataset(dataset_path):
    """
    Loads one dataset folder:
    - all CSVs
    - participants.tsv
    - merges metadata
    """
    
    
    # Data
    csv_files = list(dataset_path.glob("*.csv"))

    if not csv_files:
        raise ValueError(f"No CSV files found in {dataset_path}")

    dfs = []
    for file in csv_files:
        df = pd.read_csv(file)

        participant_id = file.stem.split("_")[0] # sub-amu01_T2w_PAM50.csv -> sub-amu01
        df["participant_id"] = participant_id

        dfs.append(df)

    if not dfs:
        raise ValueError(f"No valid CSV data in {dataset_path}")
    df_all = pd.concat(dfs, ignore_index=True)


    # Metadata
    tsv_file = dataset_path / "participants.tsv"
    if not tsv_file.exists():
        raise ValueError(f"No participants.tsv in {dataset_path}")

    mdf = pd.read_csv(tsv_file, sep="\t")

    # Merge
    df_merged = df_all.merge(mdf, on="participant_id", how="left")

    return df_merged, mdf



def clean_data(metrics_df, dem_df):
    """
    Clean the df:
    - Removes NaN values
    - Convert Solidity values into percentage values
    - Computes AP/RL ratio
    - Binary index for sex
    - Index for site
    """
    
    # Data
    clean_metrics = metrics_df.dropna(subset=["MEAN(area)", "age", ]).copy()
    clean_metrics["age"] = clean_metrics["age"].astype(int)
    clean_metrics["MEAN(solidity)"] = clean_metrics["MEAN(solidity)"] * 100
    clean_metrics["MEAN(compression_ratio)"] = clean_metrics["MEAN(diameter_AP)"] / clean_metrics["MEAN(diameter_RL)"]
    clean_metrics["sex_bin"] = (clean_metrics["sex"] == "F").astype(int)
    # Site encoding
    clean_metrics["site_id"] = (clean_metrics["institution"].astype("category").cat.codes)

    # clean["vendor_id"] = (clean["manufacturer"].astype("category").cat.codes)
    
    # Meta data  
    clean_dem = dem_df.copy()  
    clean_dem["sex"] = clean_dem["sex"].fillna("Unspecified")
    clean_dem["sex"] = clean_dem["sex"].replace({"M": "Male", "F": "Female"})

    return clean_metrics, clean_dem



def run_parsing_pipeline():
    path = fetch_normative_database()
    datasets = find_datasets(path)
    
    metrics_dfs = []
    dem_dfs = []
        
    for folder in datasets:
        data_df, meta_df = load_dataset(folder)
        
        metrics_dfs.append(data_df)
        
        meta_df["dataset_name"] = Path(folder).resolve().name
        dem_dfs.append(meta_df)

    metrics_df_all = pd.concat(metrics_dfs, ignore_index=True)
    dem_df_all = pd.concat(dem_dfs, ignore_index=True)

    return clean_data(metrics_df_all, dem_df_all)
