"""
This script handles the processing pipeline.
It deals with the demographics data by computing statistics summaries
It deals with the normative pipeline, by:
- Using neuroComBat to account for the site effects
- Fitting a Gam for each metric
- Generating a prediction grid across age, slice level, and sex
- Producing normative trajectories for each metric across the prediction grid
"""

from pygam import LinearGAM, s, f
import numpy as np
import pandas as pd
import itertools
from neuroCombat import neuroCombat
from config.metrics import METRICS

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

# NORMATIVE
def combat_harmonization(df, metrics=METRICS, site_col="site_id"):
    """
    Harmonize metrics across acquisition sites using neuroCombat.
    Returns a df with harmonized metrics.
    """

    # neuroCombat expects:
    # rows = features
    # columns = subjects
    # Shape: (n_features, n_subjects)
    data = df[metrics].T.values

    # Covariates to preserve
    covars = df[[
        site_col,
        "sex_bin",
        "age",
        "Slice (I->S)"
    ]].copy()

    # neuroCombat does not infer covariate types — any column in `covars` not
    # listed in categorical_cols or continuous_cols is silently dropped from
    # the design matrix and its effect is NOT preserved.
    categorical_cols = [
        "sex_bin"
    ]

    continuous_cols = [
        "age",
        "Slice (I->S)"
    ]

    # Run ComBat
    combat_output = neuroCombat(
        dat=data,
        covars=covars,
        batch_col=site_col,
        categorical_cols=categorical_cols,
        continuous_cols=continuous_cols
    )

    harmonized_data = combat_output["data"]

    # Back to dataframe shape
    df_harmonized = df.copy()
    df_harmonized[metrics] = harmonized_data.T

    return df_harmonized


def fit_gam(df, metric):
    """
    Returns a model for the chosen metric
    """
    
    X = df[["age", "Slice (I->S)", "sex_bin"]].values
    y = df[metric].values #data of the specified metric

    gam = LinearGAM(
        s(0) +          # age
        s(1) +          # slice
        f(2)            # sex

    ).fit(X, y)

    return gam


def fit_all_gams(df):
    models = {} # Dictionary containing for each metric (key) a model (value)

    for metric in METRICS:
        models[metric] = fit_gam(df, metric)

    return models


def create_prediction_grid(df):
    """
    Create a prediction grid
    """
    ages = range(df["age"].min(), df["age"].max())
    slices = range(df["Slice (I->S)"].min(), df["Slice (I->S)"].max())
    sexes = (0, 1)

    grid = np.array(
        list(itertools.product(
            ages,
            slices,
            sexes
        ))
    )

    return pd.DataFrame(grid, columns=["age", "Slice (I->S)", "sex_bin"])


def normative_model(models, grid, df):
    """
    Predict all metrics on the grid
    """

    results = grid.copy()

    X = results[["age", "Slice (I->S)", "sex_bin"]].values

    for metric, gam in models.items():

        results[f"{metric}"] = gam.predict(X)
        
    slice_to_vert = df[["Slice (I->S)", "VertLevel"]].drop_duplicates().set_index("Slice (I->S)")["VertLevel"].to_dict()
    results["VertLevel"] = results["Slice (I->S)"].map(slice_to_vert)

    return results

def run_normative(df):
    # Harmonization
    df_harmonized = combat_harmonization(df)

    # Fitting gam model for each metric
    models = fit_all_gams(df_harmonized)

    # Fitting on new data
    grid = create_prediction_grid(df_harmonized)
    df_norm = normative_model(models, grid, df)

    return df_norm


    
