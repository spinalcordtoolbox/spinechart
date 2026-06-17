"""
This script contains the plotting functions.
It creates interactive plots using Plotly for:
- age profile
- spinal profile
"""


import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

import numpy as np
import pandas as pd
from config.metrics import METRIC_CONFIG
from config.plotting import COLORS_SEX
from config.demographics import SEX_MAP, AGE_DECADE_MAP
from config.anatomy import VERT_DICT


def plot_heatmap(df, raw_metrics_df, metric, sex):
    if sex != "All":
        dff = df[df["sex_bin"]==SEX_MAP[sex]].copy()
        dff_raw = raw_metrics_df[raw_metrics_df["sex_bin"]==SEX_MAP[sex]].copy()
    else:
        dff = df.copy()
        dff_raw = raw_metrics_df.copy()
        
    bins = [10, 20, 30, 40, 50, 60]
    labels =  list(AGE_DECADE_MAP.keys()) #AGE_DECADES #
    
    # Convert ages to groups of age ranges
    dff["age_decade"] = pd.cut(
        dff["age"],
        bins=bins,
        labels=labels,
        include_lowest=True
    )
    
    heatmap_df = (
        dff.groupby(
            ["age_decade", "Slice (I->S)"],
            observed=False
        )[metric]
        .mean()
        .reset_index()
    )
    
    pivot = heatmap_df.pivot(
        index="age_decade",
        columns="Slice (I->S)",
        values=metric
    )
    
    
    # compute subgroup size
    dff_raw["age_decade"] = pd.cut(
        dff_raw["age"],
        bins=bins,
        labels=labels,
        include_lowest=True
    )
    
    dff_n = (
        dff_raw.groupby(
            ["age_decade", "Slice (I->S)"],
            observed=False
        )["participant_id"]
        .nunique()
        .reset_index(name="N")
    )

    pivot_n = dff_n.pivot(
        index="age_decade",
        columns="Slice (I->S)",
        values="N"
    )

    # Align N matrix to metric matrix
    pivot_n = pivot_n.reindex(
        index=pivot.index,
        columns=pivot.columns
    )

    cfg = METRIC_CONFIG[metric]
    
    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale="Viridis",
            colorbar={"title": cfg["axis"]},
            customdata=pivot_n.values[..., np.newaxis],
            hovertemplate=(
                "Age: %{y}<br>"
                "Slice: %{x}<br>"
                "Value: %{z:.2f}<br>"
                "N: %{customdata[0]:.0f}"
                "<extra></extra>"
                )
        )
    )

    fig.update_layout(
        title=f"{cfg['title']} heatmap",
        xaxis_title="Slice",
        yaxis_title="Age decade",
    )
    
    xmin = df["Slice (I->S)"].min()
    xmax = df["Slice (I->S)"].max()
    fig.update_xaxes(
        range=[xmax, xmin],
        linecolor="darkslategray",
        )
    
    # Add vertebral boundary lines
    ticks, mids, labels = get_vert_ticks(dff)
    for t in ticks:

        fig.add_vline(
            x=t,
            line_width=1,
            line_dash="dot",
            line_color="whitesmoke",
            opacity=0.8
        )
        
    # Vertebral labels annotations
    for x, label in zip(mids, labels):

        fig.add_annotation(
            x=x,
            y=0,
            xref="x",
            yref="paper",
            text=label,
            showarrow=False,
            font=dict(size=12, color="whitesmoke")
        )

    return fig


def plot_age_profile(df, raw_metrics_df, metric, level, sex):
    # compute mean per age and sex
    dff = df[
        (df["VertLevel"]==level)
        & (df["sex_bin"].isin(sex))
    ]
    dff_mean = (
        dff.groupby(["age", "sex_bin"], as_index=False)[metric]
        .mean()
        .sort_values("age")
    )
    
    # compute subgroup size
    dff_raw = raw_metrics_df[
        (raw_metrics_df["VertLevel"]==level)
        & (raw_metrics_df["sex_bin"].isin(sex))
    ]
    dff_n = (
        dff_raw.groupby(["age", "sex_bin"])["participant_id"]
        .nunique()
        .reset_index(name="N")
    )
    
    # Merge mean and subgroup size df
    dff_plot = dff_mean.merge(
        dff_n,
        on=["age", "sex_bin"],
        how="left"
    )
    dff_plot["N"] = dff_plot["N"].fillna(0).astype(int)


    fig = go.Figure()
    
    cfg = METRIC_CONFIG[metric]

    # Add a trace for each sex
    for s in sex:
        dffs = dff_plot[dff_plot["sex_bin"] == s]
        label = "Male" if s == 0 else "Female"

        fig.add_trace(go.Scatter(
            x=dffs["age"],
            y=dffs[metric],
            mode="lines",
            name=label,
            line=dict(width=3, color=COLORS_SEX[s]),
            customdata=dffs[["N"]],
            hovertemplate=(
                "Age: %{x}<br>"
                "Mean: %{y:.2f}<br>"
                "N: %{customdata[0]}"
                "<extra></extra>"
            )
        ))

    fig.update_layout(
        title=f"{cfg['title']} vs Age ({VERT_DICT[level]})",
        xaxis_title="Age (years)",
        yaxis_title=cfg['axis']
    )
    
    fig.update_yaxes(
        range=cfg['ylim'],
        showgrid=True
    )

    return fig


def plot_spinal_profile(df, raw_metrics_df, metric, age, sex):
    # compute mean per slice and sex
    dff = df[(df["age"].between(age[0], age[1])) & df["sex_bin"].isin(sex)]
    dff_mean = (
        dff.groupby(["Slice (I->S)", "sex_bin"], as_index=False)[metric]
        .mean()
        .sort_values("Slice (I->S)")
    )
    
    # compute subgroup size
    dff_raw = raw_metrics_df[(raw_metrics_df["age"].between(age[0], age[1])) & raw_metrics_df["sex_bin"].isin(sex)]
    dff_n = (
        dff_raw.groupby(["Slice (I->S)", "sex_bin"])["participant_id"]
        .nunique()
        .reset_index(name="N")
    )
    
    # Merge mean and subgroup size df
    dff_plot = dff_mean.merge(
        dff_n,
        on=["Slice (I->S)", "sex_bin"],
        how="left"
    )
    dff_plot["N"] = dff_plot["N"].fillna(0).astype(int)
    

    fig = go.Figure()
    
    cfg = METRIC_CONFIG[metric]

    # Add a trace for each sex
    for s in sex:
        dffs = dff_plot[dff_plot["sex_bin"] == s]

        label = "Male" if s == 0 else "Female"

        fig.add_trace(go.Scatter(
            x=dffs["Slice (I->S)"],
            y=dffs[metric],
            name=label,
            mode="lines",
            line=dict(width=3, color=COLORS_SEX[s]),
            customdata=dffs[["N"]],
            hovertemplate=(
                "Slice: %{x}<br>"
                "Mean: %{y:.2f}<br>"
                "N: %{customdata[0]}"
                "<extra></extra>"
            )
        ))
        
    # Add vertebral boundary lines
    ticks, mids, labels = get_vert_ticks(dff)
    for t in ticks:

        fig.add_vline(
            x=t,
            line_width=1,
            line_dash="dot",
            line_color="gray",
            opacity=0.8
        )

    # Vertebral labels annotations
    for x, label in zip(mids, labels):

        fig.add_annotation(
            x=x,
            y=0,
            xref="x",
            yref="paper",
            text=label,
            showarrow=False,
            font=dict(size=12, color="gray")
        )
    
    fig.update_layout(
        title=f"{cfg['title']} vs Slice (Age {age[0]} to {age[1]})",
        xaxis_title="Slice",
        yaxis_title=cfg['axis']
    )
    
    xmin = df["Slice (I->S)"].min()
    xmax = df["Slice (I->S)"].max()
    fig.update_xaxes(
        range=[xmax, xmin],
        linecolor="darkslategray",
        )
    
    fig.update_yaxes(
        range=cfg['ylim'],
        showgrid=True
    )
    
    return fig


def get_vert_ticks(df):
    """
    Get vertebral boundary ticks and midpoint labels for plotting.

    Args:
        df (pd.DataFrame): dataframe comprising 'Slice (I->S)' and 'VertLevel' columns

    Returns:
        vert_ticks (np.array):
            Slice positions where vertebral levels change

        vert_mid (list):
            Mid-slice positions for vertebral labels

        vert_labels (list):
            Vertebral labels (C1, C2, ...)
    """

    # Sort anatomically
    df = df.sort_values("Slice (I->S)").reset_index(drop=True)

    # Keep one row per slice
    df = df[["Slice (I->S)", "VertLevel"]].drop_duplicates()

    # Detect vertebral transitions
    change_mask = df["VertLevel"].diff() != 0

    # Beginning slice of each vertebra
    vert_starts = df.loc[change_mask, "Slice (I->S)"].values

    # Vertebral numeric levels
    vert_levels = df.loc[change_mask, "VertLevel"].values

    # Add final slice
    boundaries = np.append(vert_starts, df["Slice (I->S)"].iloc[-1])

    # Midpoints between vertebral boundaries
    vert_mid = []

    for i in range(len(boundaries) - 1):
        mid = (boundaries[i] + boundaries[i + 1]) / 2
        vert_mid.append(mid)

    # Convert numeric levels to labels
    vert_labels = [VERT_DICT.get(v, str(v)) for v in vert_levels]
    
    return vert_starts[1:], vert_mid, vert_labels


def plot_age_raincloud(df):
    dff = (
        df[["participant_id", "dataset_name", "sex", "age"]]
        .dropna(subset=["age", "sex"])
    )

    # Dataset ordering
    dataset_order = (
        dff.groupby("dataset_name")["age"]
        .median()
        .sort_values()
        .index
        .tolist()
    )

    sexes = sorted(dff["sex"].unique())

    # Colors per sex
    colors = {
        sex: f"hsl({i * 360 / len(sexes)}, 60%, 55%)"
        for i, sex in enumerate(sexes)
    }

    # Spacing between sexes
    sex_offsets = {
        sex: (i - (len(sexes) - 1) / 2) * 0.35
        for i, sex in enumerate(sexes)
    }
    
    fig = go.Figure()

    jitter_strength = 0.12

    for i, dataset in enumerate(dataset_order):
        subset = dff[dff["dataset_name"] == dataset]

        for sex in sexes:
            sub = subset[subset["sex"] == sex]
            if sub.empty:
                continue
            
            # Applying offset
            x_base = i + sex_offsets[sex]
            
            # Tooltip
            n = (
                sub.groupby("age")["participant_id"]
                .nunique()
                .rename("N")
                .reset_index()
            )
            sub = sub.merge(n, on="age", how="left")
            customdata = np.stack([
                sub["dataset_name"],
                sub["sex"],
                sub["N"]
            ], axis=-1)
            
            hovertemplate_jitter = (
                "Dataset: %{customdata[0]}<br>"
                "Sex: %{customdata[1]}<br>"
                "Age: %{y}<br>"
                "N:  %{customdata[2]}<extra></extra>"
                )
            
            # Half-violin
            fig.add_trace(go.Violin(
                x=[x_base] * len(sub),
                y=sub["age"],
                side="positive",
                customdata=customdata,
                hoverlabel=dict(namelength=0),
                line_color="black",
                fillcolor=colors[sex],
                opacity=0.6,
                points=False,
                spanmode="hard",
                width=0.6,
                name=sex,
                legendgroup=sex,
                showlegend=(i == 0)
            ))

            # Box plot
            fig.add_trace(go.Box(
                x=[x_base] * len(sub),
                y=sub["age"],
                customdata=customdata,
                hoverlabel=dict(namelength=0),
                marker=dict(color="black", opacity=0.4),
                width=0.15,
                boxpoints=False,
                legendgroup=sex,
                showlegend=False
            ))

            # Jitter plot
            x_jittered = (
                np.random.uniform(-jitter_strength, jitter_strength, len(sub))
                + x_base
            )

            fig.add_trace(go.Scatter(
                x=x_jittered,
                y=sub["age"],
                customdata=customdata,
                hovertemplate=hovertemplate_jitter,
                mode="markers",
                marker=dict(color=colors[sex], size=5, opacity=0.4),
                legendgroup=sex,
                showlegend=False
            ))

    fig.update_layout(
        title="Raincloud Plot",
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(len(dataset_order))),
            ticktext=dataset_order,
            title="Dataset"
        ),
        yaxis_title="Age (years)",
        showlegend=True
    )

    return fig