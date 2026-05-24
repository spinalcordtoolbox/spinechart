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
    Finds all dataset folders containing CSV + participants.tsv
    """
    dataset_dir = (
        root
        / "spinal_cord"
        / "spine-generic_multi-subject"
    )

    if not dataset_dir.exists():
        raise ValueError(f"Dataset folder not found: {dataset_dir}")

    required_files = [
        dataset_dir / "participants.tsv",
        dataset_dir / "dataset_description.json",
    ]

    has_required = all(f.exists() for f in required_files)
    has_csv = any(dataset_dir.glob("*.csv"))

    if not (has_required and has_csv):
        raise ValueError(f"Invalid dataset structure in: {dataset_dir}")

    return [dataset_dir]



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

    return df_merged



def clean_data(df):
    """
    Clean the df:
    - Removes NaN values
    - Convert Solidity values into percentage values
    - Computes AP/RL ratio
    - Binary index for sex
    - Index for site
    """
    clean = df.dropna(subset=["MEAN(area)", "age", ]).copy()
    
    clean["MEAN(solidity)"] = clean["MEAN(solidity)"] * 100
    
    clean["MEAN(compression_ratio)"] = clean["MEAN(diameter_AP)"] / clean["MEAN(diameter_RL)"]

    clean["sex_bin"] = (clean["sex"] == "F").astype(int)

    # Site encoding
    clean["site_id"] = (clean["institution"].astype("category").cat.codes)

    # clean["vendor_id"] = (clean["manufacturer"].astype("category").cat.codes)

    return clean



def run_parsing_pipeline():
    path = fetch_normative_database()
    datasets = find_datasets(path)
    
    dfs = []
    for folder in datasets:
        df = load_dataset(folder)
        dfs.append(df)

    df_all = pd.concat(dfs, ignore_index=True)

    return clean_data(df_all)
