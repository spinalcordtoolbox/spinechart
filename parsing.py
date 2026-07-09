import zipfile
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests
from tqdm import tqdm

from config.metrics import METRICS

# Update this for each release
MODEL_RELEASE = "r20260709"
ZIP_NAME = "Source code (zip)"

RELEASE_URL = (
    "https://github.com/spinalcordtoolbox/PAM50-normalized-metrics/"
    f"archive/refs/tags/{MODEL_RELEASE}.zip"
)

DATA_ROOT = Path("data/")


def fetch_normative_database(url=RELEASE_URL, local_path=DATA_ROOT):
    """
    Downloads the normative database if it does not exist.

    Returns
    -------
    Path
        Local path to the repository.
    """
    if Path(f"{local_path}/PAM50-normalized-metrics-{MODEL_RELEASE}").exists():
        print(f"{local_path}/PAM50-normalized-metrics-{MODEL_RELEASE} already exists.")
        return local_path / f"PAM50-normalized-metrics-{MODEL_RELEASE}"
    
    print(f"Downloading PAM50-normalized-metrics release {MODEL_RELEASE}...")

    local_path.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))
    zip_path = local_path / "release.zip"

    with (
        zip_path.open("wb") as f,
        tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc="Downloading data",
        ) as pbar,
    ):
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))

    print("Extracting...")

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(local_path)

    zip_path.unlink()

    return local_path / f"PAM50-normalized-metrics-{MODEL_RELEASE}"



def find_datasets(root):
    """
    Finds dataset folders containing CSV + participants.tsv
    (Currently only spine-generic_multi-subject and whole-spine)
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
    mdf["dataset_name"] = Path(dataset_path).resolve().name

    # Merge
    df_merged = df_all.merge(mdf, on="participant_id", how="left")

    return df_merged, mdf



def clean_data(metrics_df, dem_df):
    """
    Clean the df:
    - Removes NaN values
    - Convert Solidity values into percentage values
    - Computes AP/RL ratio
    - Creates binary sex encoding
    - Creates dataset index
    """
    
    # Data
    clean_metrics = metrics_df.dropna(subset=["MEAN(area)", "age", ]).copy()
    clean_metrics["age"] = clean_metrics["age"].astype(int)
    clean_metrics["MEAN(solidity)"] = clean_metrics["MEAN(solidity)"] * 100
    clean_metrics["MEAN(compression_ratio)"] = clean_metrics["MEAN(diameter_AP)"] / clean_metrics["MEAN(diameter_RL)"]
    clean_metrics["sex_bin"] = (clean_metrics["sex"] == "F").astype(int)
    # Dataset encoding
    clean_metrics["dataset_id"] = (clean_metrics["dataset_name"].astype("category").cat.codes)
    # No 0 values (not accepted in BCT distribution)
    clean_metrics[METRICS] = clean_metrics[METRICS].replace(0, 1e-6)
    
    # Meta data  
    clean_dem = dem_df.dropna(subset=["sex", ]).copy()
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
        
        dem_dfs.append(meta_df)

    metrics_df_all = pd.concat(metrics_dfs, ignore_index=True)
    dem_df_all = pd.concat(dem_dfs, ignore_index=True)

    return clean_data(metrics_df_all, dem_df_all)