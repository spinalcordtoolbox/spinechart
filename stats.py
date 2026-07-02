"""
This script computes statistics summaries for the demographics data.
"""

# DEMOGRAPHICS
def summary_dataset(dem_df):
    """Compute demographic summary statistics by dataset.

    Args:
        dem_df (pd.DataFrame): dataframe containing metadata

    Returns:
        pd.DataFrame: dataframe containing summary statistics grouped by dataset
    """
    # Dataset overview table
    dataset_summary = (
        dem_df.groupby("dataset_name")
        .agg(
            N=("participant_id", "nunique"),
            Mean_Age=("age", "mean"),
            STD_Age=("age", "std"),
            Min_Age=("age", "min"),
            Max_Age=("age", "max"),
        )
        .reset_index()
    )

    dataset_summary["Mean_Age"] = dataset_summary["Mean_Age"].round(1)
    dataset_summary["STD_Age"] = dataset_summary["STD_Age"].round(1)
    return dataset_summary

def summary_pathology(dem_df):
    """Compute demographic summary statistics by pathology.

    Args:
        dem_df (pd.DataFrame): dataframe containing metadata

    Returns:
        pd.DataFrame: dataframe containing summary statistics grouped by pathology
    """
    # Pathology overview table
    pathology_summary = (
        dem_df.groupby("pathology")
        .agg(
            N=("participant_id", "nunique"),
            Mean_Age=("age", "mean"),
            STD_Age=("age", "std"),
            Min_Age=("age", "min"),
            Max_Age=("age", "max"),
        )
        .reset_index()
        .sort_values("N", ascending=False)
    )

    pathology_summary["Mean_Age"] = pathology_summary["Mean_Age"].round(1)
    pathology_summary["STD_Age"] = pathology_summary["STD_Age"].round(1)
    
    return pathology_summary

    
