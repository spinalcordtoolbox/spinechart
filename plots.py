"""
This script contains the plotting functions.
It creates interactive plots using Plotly for:
- heatmap
- age profile
- spinal profile
- age demographics rainclouds
"""

import plotly.graph_objects as go
import numpy as np
import pandas as pd

from config.metrics import METRIC_CONFIG
from config.plotting import COLORS_SEX
from config.demographics import SEX_MAP, AGE_DECADE_MAP
from config.anatomy import VERT_DICT


# ---------------------------------------------------------------------------
# Centile band helpers
# ---------------------------------------------------------------------------

_CENTILE_BAND_PAIRS = [(5, 95, 0.08), (10, 90, 0.13), (25, 75, 0.20)]

def _hex_to_rgba(hex_color, alpha):
    """Converts hexadecimal color string to CSS color string format.

    Args:
        hex_color (str): hexadecimal color string
        alpha (float): opacity

    Returns:
        (str): CSS color string
    """
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def _add_centile_bands(fig, centile_agg, x_col, color, sex_label):
    """ Overlay shaded centile bands and a solid median onto fig.

    Args:
        fig (plotly.graph_objects.Figure): figure to which the centile bands and median line are added.
        centile_agg (pd.DataFrame): aggregated centile data obtained after running run_normative_pipeline.py
        x_col (str): name of the x-axis column (age/slice_idx)
        color (str):  hexadecimal color string used for the 50th centile line and shaded bands.
        sex_label (str): "Male" or "Female"
    """
    
    first_band = True

    for lo, hi, alpha in _CENTILE_BAND_PAIRS:
        col_lo, col_hi = f"centile_{lo}", f"centile_{hi}"
        if col_lo not in centile_agg.columns or col_hi not in centile_agg.columns:
            continue

        # Lower anchor
        fig.add_trace(go.Scatter(
            x=centile_agg[x_col], y=centile_agg[col_lo],
            mode="lines", line=dict(width=0),
            showlegend=False, hoverinfo="skip",
        ))
        #  Add the upper boundary and fill the area down to the previous trace.
        fig.add_trace(go.Scatter(
            x=centile_agg[x_col], y=centile_agg[col_hi],
            mode="lines", line=dict(width=0),
            fill="tonexty",
            fillcolor=_hex_to_rgba(color, alpha),
            name=f"5th-95th ({sex_label})" if first_band else None,
            showlegend=first_band,
            hoverinfo="skip",
        ))
        first_band = False

    # Overlay the 50th centile as a solid line.
    if "centile_50" in centile_agg.columns:
        fig.add_trace(go.Scatter(
            x=centile_agg[x_col], y=centile_agg["centile_50"],
            mode="lines",
            line=dict(width=2.5, color=color),
            name=f"Median ({sex_label})",
            customdata=centile_agg["N"],
            hovertemplate=(
                f"50th centile ({sex_label})<br>"
                f"{x_col}: %{{x}}<br>"
                "Value: %{y:.2f}<br>"
                "N: %{customdata:.0f}"
                "<extra></extra>"
            ),
        ))


# ---------------------------------------------------------------------------
# Heatmap (centile_50 across age and slice)
# ---------------------------------------------------------------------------

def plot_heatmap(curves, metrics_df, metric, sex) :
    """Plot heatmap

    Args:
        curves (pd.DataFrame): centile_curves for the given metric
        metrics_df (pd.DataFrame): raw metric data (for N counts and VertLevel annotations)
        metric (str): metric name
        sex (str): sexes selected
    Returns:
        go.Figure: heatmap
    """

    cfg  = METRIC_CONFIG[metric]
    bins = [10, 20, 30, 40, 50, 60]
    age_labels = list(AGE_DECADE_MAP.keys())

    # Filter by sex
    if sex != "All":
        dfc = curves[curves["sex_bin"] == SEX_MAP[sex]].copy()
        dfr = metrics_df[metrics_df["sex_bin"] == SEX_MAP[sex]].copy()
    else:
        dfc = curves.copy()
        dfr = metrics_df.copy()

    # Bin age into decades
    dfc["age_decade"] = pd.cut(dfc["age"], bins=bins, labels=age_labels, include_lowest=True)

    # Average centile_50 across sex_bin when sex=="All"
    heat_df = (
        dfc.groupby(["age_decade", "slice_idx"], observed=False)["centile_50"]
        .mean()
        .reset_index()
    )
    pivot = heat_df.pivot(index="age_decade", columns="slice_idx", values="centile_50")

    # N counts from raw data
    dfr["age_decade"] = pd.cut(dfr["age"], bins=bins, labels=age_labels, include_lowest=True)
    dff_n = (
        dfr.groupby(["age_decade", "Slice (I->S)"], observed=False)["participant_id"]
        .nunique()
        .reset_index(name="N")
        .rename(columns={"Slice (I->S)": "slice_idx"})
    )
    pivot_n = (
        dff_n.pivot(index="age_decade", columns="slice_idx", values="N")
        .reindex(index=pivot.index, columns=pivot.columns)
    )

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale="Viridis",
        colorbar={"title": cfg["axis"]},
        zmin=cfg["ylim"][0],
        zmax=cfg["ylim"][1],
        customdata=pivot_n.values[..., np.newaxis],
        hovertemplate=(
            "Age: %{y}<br>Slice: %{x}<br>"
            "Value: %{z:.2f}<br>"
            "N: %{customdata[0]:.0f}"
            "<extra></extra>"
        ),
    ))

    fig.update_layout(
        title=f"{cfg['title']} heatmap",
        xaxis_title="PAM50 Slice #",
        yaxis_title="Age decade",
    )

    xmin = metrics_df["Slice (I->S)"].min()
    xmax = metrics_df["Slice (I->S)"].max()
    fig.update_xaxes(range=[xmax, xmin], linecolor="darkslategray")

    # Add vertebral boundary lines
    ticks, mids, vlabels = get_vert_ticks(dfr)
    for t in ticks:
        fig.add_vline(x=t, line_width=1, line_dash="dot", line_color="whitesmoke", opacity=0.8)
    # Vertebral level names annotations
    for x, label in zip(mids, vlabels):
        fig.add_annotation(x=x, y=0, xref="x", yref="paper",
                           text=label, showarrow=False,
                           font=dict(size=12, color="whitesmoke"))
    return fig


# ---------------------------------------------------------------------------
# Age profile
# ---------------------------------------------------------------------------

def plot_age_profile(curves, metrics_df, metric, level, sex, slice_vert_map, show_normative=True, aligned_cohort=None, aligned_patient=None):
    """Plot the spinal profile, with centile curves

    Args:
        curves (pd.DataFrame): centile_curves for the given metric
        metrics_df (pd.DataFrame): raw metric data (for N counts and VertLevel annotations)
        metric (str): metric name
        sex (list): sexes selected
        slice_vert_map : {slice_idx: VertLevel} dict built from metrics_df
        show_normative (bool): show normative plots if option selected in checkbox
        aligned_cohort: show cohort data points if option selected in checkbox
        aligned_patient: show patient data point if option selected in checkbox

    Returns:
        go.Figure: age profile
    """

    cfg = METRIC_CONFIG[metric]
    fig = go.Figure()

    # Slices that belong to this VertLevel
    level_slices = {s for s, v in slice_vert_map.items() if v == level}

    for s in sex:
        color     = COLORS_SEX[s]
        sex_label = "Male" if s == 0 else "Female"

        dfc = curves[
            curves["slice_idx"].isin(level_slices) &
            (curves["sex_bin"] == s)
        ]
        if dfc.empty:
            continue

        # Average centile columns across slices within this vertebral level
        if show_normative:
            centile_cols = [c for c in dfc.columns if c.startswith("centile_")]
            centile_agg  = (
                dfc.groupby("age")[centile_cols]
                .mean()
                .reset_index()
                .sort_values("age")
            )
            # Raw counts at each age for hovertemplate
            n_by_age = (
                metrics_df.groupby("age")["participant_id"]
                .nunique()
                .rename("N")
                .reset_index()
            )
            centile_agg = centile_agg.merge(n_by_age, on="age", how="left")
            centile_agg["N"] = centile_agg["N"].fillna(0).astype(int)

            _add_centile_bands(fig, centile_agg, x_col="age", color=color, sex_label=sex_label)

        # N counts from raw data for subtitle
        dff_raw = metrics_df[
            (metrics_df["VertLevel"] == level) &
            metrics_df["sex_bin"].isin(sex)
        ]
        n_total = dff_raw["participant_id"].nunique()
    
    if aligned_cohort is not None:
        dff = aligned_cohort[
            (aligned_cohort["slice_idx"].isin(level_slices)) &
            (aligned_cohort["sex_bin"].isin(sex))
        ]
         # Average all slices belonging to the vertebral level
        dff = dff.groupby(["participant_id", "age", "sex_bin"], as_index=False)["value"].mean()

        fig.add_trace(
            go.Scatter(
                x=dff["age"],
                y=dff["value"],
                mode="markers",
                name="Aligned cohort",
                marker=dict(
                    color="black",
                    size=6,
                    opacity=0.35,
                ),
                customdata=dff["participant_id"],
                hovertemplate=(
                    "Subject: %{customdata}<br>"
                    "Age: %{x:.1f}<br>"
                    "Value: %{y:.2f}<extra></extra>"
                )
            )
        )
    
    if aligned_patient is not None:

        dff = aligned_patient[aligned_patient["slice_idx"].isin(level_slices)]
        dff = dff.groupby(["participant_id", "age"], as_index=False)["value"].mean()

        fig.add_trace(
            go.Scatter(
                x=dff["age"],
                y=dff["value"],
                mode="markers",
                name="Patient",
                marker=dict(
                    color="red",
                    size=10,
                    symbol="diamond"
                ),
            )
        )
    

    fig.update_layout(
        title=f"{cfg['title']} vs Age ({VERT_DICT[level]})<br><sup>N = {n_total}</sup>",
        xaxis_title="Age (years)",
        yaxis_title=cfg["axis"],
    )
    fig.update_yaxes(range=cfg["ylim"], showgrid=True)
    return fig


# ---------------------------------------------------------------------------
# Spinal profile
# ---------------------------------------------------------------------------

def plot_spinal_profile(curves, metrics_df, metric, age, sex, show_normative=True, aligned_cohort=None, aligned_patient=None):
    """Plot the spinal profile, with centile curves

    Args:
        curves (pd.DataFrame): centile_curves for the given metric
        metrics_df (pd.DataFrame): raw metric data (for N counts and VertLevel annotations)
        metric (str): metric name
        age (list): age range selected
        sex (list): sexes selected
        show_normative (bool): show normative plots if option selected in checkbox
        aligned_cohort: show cohort data points if option selected in checkbox
        aligned_patient: show patient data point if option selected in checkbox

    Returns:
        go.Figure: spinal profile
    """
    
    cfg = METRIC_CONFIG[metric]
    fig = go.Figure()

    for s in sex:
        color     = COLORS_SEX[s]
        sex_label = "Male" if s == 0 else "Female"

        dfc = curves[
            curves["age"].between(age[0], age[1]) &
            (curves["sex_bin"] == s)
        ]
        if dfc.empty:
            continue

        # Average centile columns across the age range at each slice
        if show_normative:
            centile_cols = [c for c in dfc.columns if c.startswith("centile_")]
            centile_agg  = (
                dfc.groupby("slice_idx")[centile_cols]
                .mean()
                .reset_index()
                .sort_values("slice_idx")
            )
            
            dfc = curves[
                curves["age"].between(age[0], age[1]) &
                (curves["sex_bin"] == s)
            ]
            
            # Raw N count for each slice for hovertemplate
            n_by_slice = (
                metrics_df[
                    metrics_df["age"].between(age[0], age[1]) &
                    (metrics_df["sex_bin"] == s)
                ]
                .groupby("Slice (I->S)")["participant_id"]
                .nunique()
                .rename("N")
            )

            centile_agg["N"] = centile_agg["slice_idx"].map(n_by_slice).fillna(0).astype(int)

            _add_centile_bands(fig, centile_agg, x_col="slice_idx", color=color, sex_label=sex_label)
            
    if aligned_cohort is not None:
        dff = aligned_cohort[
            (aligned_cohort["age"].between(age[0], age[1])) &
            (aligned_cohort["sex_bin"].isin(sex))
        ]
         # Average all slices belonging to the vertebral level
        for pid, sub in dff.groupby("participant_id"):

            sub = sub.sort_values("slice_idx")

            fig.add_trace(
                go.Scatter(
                    x=sub["slice_idx"],
                    y=sub["value"],
                    mode="lines",
                    line=dict(
                        color="black",
                        width=1,
                    ),
                    opacity=0.25,
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
    
    if aligned_patient is not None:
        
        dff = aligned_patient.sort_values("slice_idx")

        fig.add_trace(
            go.Scatter(
                x=dff["slice_idx"],
                y=dff["value"],
                mode="lines",
                name="Patient",
                line=dict(
                    color="red",
                    width=3,
                ),
                marker=dict(size=6),
            )
        )

    # Vertebral annotations from the raw data for subtitle
    dff_raw = metrics_df[
        metrics_df["age"].between(age[0], age[1]) &
        metrics_df["sex_bin"].isin(sex)
    ]
    if not dff_raw.empty:
        ticks, mids, vlabels = get_vert_ticks(dff_raw)
        for t in ticks:
            fig.add_vline(x=t, line_width=1, line_dash="dot",
                          line_color="gray", opacity=0.8)
        for x, label in zip(mids, vlabels):
            fig.add_annotation(x=x, y=0, xref="x", yref="paper",
                               text=label, showarrow=False,
                               font=dict(size=12, color="gray"))

    
    n_total = dff_raw["participant_id"].nunique() if not dff_raw.empty else 0
    xmin = metrics_df["Slice (I->S)"].min()
    xmax = metrics_df["Slice (I->S)"].max()

    fig.update_layout(
        title=f"{cfg['title']} vs Slice (Age {age[0]}-{age[1]})<br><sup>N = {n_total}</sup>",
        xaxis_title="PAM50 Slice #",
        yaxis_title=cfg["axis"],
    )
    fig.update_xaxes(range=[xmax, xmin], linecolor="darkslategray")
    fig.update_yaxes(range=cfg["ylim"], showgrid=True)
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