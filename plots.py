"""
This script contains the plotting functions.
It creates interactive plots using Plotly for:
- age profile
- spinal profile
"""


import plotly.graph_objects as go
import numpy as np


METRICS = ['MEAN(area)', 'MEAN(diameter_AP)', 'MEAN(diameter_RL)', 'MEAN(compression_ratio)', 'MEAN(eccentricity)',
           'MEAN(solidity)']

METRICS_DTYPE = {
    'MEAN(diameter_AP)': 'float64',
    'MEAN(area)': 'float64',
    'MEAN(diameter_RL)': 'float64',
    'MEAN(eccentricity)': 'float64',
    'MEAN(solidity)': 'float64',
}

METRIC_TO_TITLE = {
    'MEAN(diameter_AP)': 'AP Diameter',
    'MEAN(area)': 'Cross-Sectional Area',
    'MEAN(diameter_RL)': 'Transverse Diameter',
    'MEAN(compression_ratio)': 'AP/RL Ratio',
    'MEAN(eccentricity)': 'Eccentricity',
    'MEAN(solidity)': 'Solidity',
}

METRIC_TO_AXIS = {
    'MEAN(diameter_AP)': 'AP Diameter [mm]',
    'MEAN(area)': 'Cross-Sectional Area [mm²]',
    'MEAN(diameter_RL)': 'Transverse Diameter [mm]',
    'MEAN(compression_ratio)': 'AP/RL Ratio [a.u.]',
    'MEAN(eccentricity)': 'Eccentricity [a.u.]',
    'MEAN(solidity)': 'Solidity [%]',
}

DEMOGRAPHIC_TO_AXIS = {
    'age': 'Age [years]',
    'BMI': 'BMI [kg/m²]',
    'height': 'Height [cm]',
    'weight': 'Weight [kg]',
}

# ylim max offset (used for showing text)
METRICS_TO_YLIM_OFFSET = {
    'MEAN(diameter_AP)': 0.4,
    'MEAN(area)': 6,
    'MEAN(diameter_RL)': 0.7,
    'MEAN(eccentricity)': 0.03,
    'MEAN(compression_ratio)': 0.03,
    'MEAN(solidity)': 1,
}

# Set ylim to do not overlap horizontal grid with vertebrae labels
METRICS_TO_YLIM = {
    'MEAN(diameter_AP)': (4, 10), #(10, 20), #TODO: use second value for canal
    'MEAN(area)': (20, 95),  #(100, 270),
    'MEAN(diameter_RL)': (6, 14.5), #(15, 35),
    'MEAN(compression_ratio)': (0.41, 0.84),
    'MEAN(eccentricity)': (0.51, 0.89),
    'MEAN(solidity)': (0.95, 0.99),
}

DISCS_DICT = {
    7: 'C7-T1',
    6: 'C6-C7',
    5: 'C5-C6',
    4: 'C4-C5',
    3: 'C3-C4',
    2: 'C2-C3',
    1: 'C1-C2'
}

MID_VERT_DICT = {
    14: 'T7',
    13: 'T6',
    12: 'T5',
    11: 'T4',
    10: 'T3',
    9: 'T2',
    8: 'T1',
    7: 'C7',
    6: 'C6',
    5: 'C5',
    4: 'C4',
    3: 'C3',
    2: 'C2',
    1: 'C1'
}

VENDORS = ['Siemens', 'Philips', 'GE']
AGE_DECADES = ['10-20', '21-30', '31-40', '41-50', '51-60']

LABELS_FONT_SIZE = 14
TICKS_FONT_SIZE = 12

COLORS_SEX = {
    0: 'blue',
    1: 'red'
    }

# To be same as spine-generic figures (https://github.com/spine-generic/spine-generic/blob/master/spinegeneric/cli/generate_figure.py#L114)
PALETTE = {
    'sex': {'M': 'blue', 'F': 'red'},
    'manufacturer': {'Siemens': 'green', 'Philips': 'dodgerblue', 'GE': 'black'},
    'age': {'10-20': 'blue', '21-30': 'green', '31-40': 'black', '41-50': 'red', '51-60': 'purple'},
    }


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
        title=f"{METRIC_TO_TITLE[metric]} vs Age (Level {level})",
        xaxis_title="Age (years)",
        yaxis_title=METRIC_TO_AXIS[metric]
    )
    
    fig.update_yaxes(
        range=METRICS_TO_YLIM[metric],
        dtick=(METRICS_TO_YLIM[metric][1] - METRICS_TO_YLIM[metric][0]) / 5,
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
        title=f"{METRIC_TO_TITLE[metric]} vs Slice (Age {age[0]} to {age[1]})",
        xaxis_title="Slice",
        yaxis_title=METRIC_TO_AXIS[metric]
    )
    
    fig.update_xaxes(
        autorange='reversed'
    )
    
    fig.update_yaxes(
        range=METRICS_TO_YLIM[metric],
        dtick=(METRICS_TO_YLIM[metric][1] - METRICS_TO_YLIM[metric][0]) / 5,
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