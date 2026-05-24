"""
This script contains the plotting functions.
It creates interactive plots using Plotly for:
- age profile
- spinal profile
"""


import plotly.graph_objects as go
import numpy as np
from config.metrics import METRIC_CONFIG
from config.plotting import COLORS_SEX


def plot_age_profile(df, metric, level, sex):
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


    fig = go.Figure()
    
    cfg = METRIC_CONFIG[metric]

    # Add a trace for each sex
    for s in sex:
        dffs = dff_mean[dff_mean["sex_bin"] == s]
        label = "Male" if s == 0 else "Female"

        fig.add_trace(go.Scatter(
            x=dffs["age"],
            y=dffs[metric],
            mode="lines",
            name=label,
            line=dict(width=3, color=COLORS_SEX[s]),
            hovertemplate='Age : %{x}, Mean : %{y:.2f} <extra></extra>'
        ))

    fig.update_layout(
        title=f"{cfg['title']} vs Age (Level {level})",
        xaxis_title="Age (years)",
        yaxis_title=cfg['axis']
    )
    
    fig.update_yaxes(
        range=cfg['ylim'],
        showgrid=True
    )

    return fig


def plot_spinal_profile(df, metric, age, sex):
    # compute mean per slice and sex
    dff = df[(df["age"].between(age[0], age[1])) & df["sex_bin"].isin(sex)]
    dff_mean = (
        dff.groupby(["Slice (I->S)", "sex_bin"], as_index=False)[metric]
        .mean()
        .sort_values("Slice (I->S)")
    )


    fig = go.Figure()
    
    cfg = METRIC_CONFIG[metric]

     # Add a trace for each sex
    for s in sex:
        dffs = dff_mean[dff_mean["sex_bin"] == s]

        label = "Male" if s == 0 else "Female"

        fig.add_trace(go.Scatter(
            x=dffs["Slice (I->S)"],
            y=dffs[metric],
            name=label,
            mode="lines",
            line=dict(width=3, color=COLORS_SEX[s]),
            hovertemplate='Slice : %{x}, Mean : %{y:.2f} <extra></extra>'
        ))
        
    # Add vertebral boundary lines
    ticks, mids, labels = get_vert_ticks(dff)
    for t in ticks:

        fig.add_vline(
            x=t,
            line_width=1,
            line_dash="dot",
            line_color="gray"
        )

    # Horizontal separator bar
    fig.add_shape(
        type="line",
        x0=0,
        x1=1,
        y0=0,
        y1=0,
        xref="paper",
        yref="paper",
        line=dict(color="black", width=1)
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

            font=dict(size=12, color="black")
        )
    
    # Add vertebral labels
    fig.update_layout(
        title=f"{cfg['title']} vs Slice (Age {age[0]} to {age[1]})",
        xaxis_title="Slice",
        yaxis_title=cfg['axis']
    )
    
    fig.update_xaxes(
        autorange='reversed'
    )
    
    fig.update_yaxes(
        range=cfg['ylim'],
        # dtick=(METRICS_TO_YLIM[metric][1] - METRICS_TO_YLIM[metric][0]) / 5,
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
    vert_labels = [f"C{v}" if v<=7 else f"T{v-7}" for v in vert_levels]

    return vert_starts, vert_mid, vert_labels