import pandas as pd


# REPO_URL = "https://github.com/spinalcordtoolbox/PAM50-normalized-metrics.git"


def find_datasets(root):
    """
    Finds all dataset folders containing CSV + participants.tsv
    """
    datasets = []

    for dataset_dir in root.rglob("*"):
        if dataset_dir.is_dir():

            csvs = list(dataset_dir.rglob("*.csv"))
            tsv = list(dataset_dir.rglob("participants.tsv"))

            if csvs and tsv:
                datasets.append(dataset_dir)

    return datasets



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
    - Binary index for sex
    """
    clean = df.dropna(subset=["MEAN(area)", "age", ]).copy()

    clean["sex_bin"] = (clean["sex"] == "F").astype(int)

    # Site encoding
    clean["site_id"] = (clean["institution"].astype("category").cat.codes)

    # clean["vendor_id"] = (clean["manufacturer"].astype("category").cat.codes)

    return clean



def run_parsing_pipeline(path):
    datasets = find_datasets(path)
    
    dfs = []
    for folder in datasets:
        df = load_dataset(folder)
        dfs.append(df)

    df_all = pd.concat(dfs, ignore_index=True)

    return clean_data(df_all)
