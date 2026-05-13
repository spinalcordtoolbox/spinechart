import plotly.graph_objects as go


METRICS = ['MEAN(area)', 'MEAN(diameter_AP)', 'MEAN(diameter_RL)', 'MEAN(eccentricity)',
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
    'MEAN(eccentricity)': 'Eccentricity',
    'MEAN(solidity)': 'Solidity',
}

METRIC_TO_AXIS = {
    'MEAN(diameter_AP)': 'AP Diameter [mm]',
    'MEAN(area)': 'Cross-Sectional Area [mm²]',
    'MEAN(diameter_RL)': 'Transverse Diameter [mm]',
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
    'MEAN(solidity)': 1,
}

# Set ylim to do not overlap horizontal grid with vertebrae labels
METRICS_TO_YLIM = {
    'MEAN(diameter_AP)': (5.7, 9.3), #(10, 20), #TODO: use second value for canal
    'MEAN(area)': (35, 95),  #(100, 270),
    'MEAN(diameter_RL)': (8.5, 14.5), #(15, 35),
    'MEAN(eccentricity)': (0.51, 0.89),
    'MEAN(solidity)': (91.2, 99.9),
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


def plot_age_profile(df, metric, slice, sex):
    # compute mean per age and sex
    dff = df[
        (df["Slice (I->S)"] == slice)
        & (df["sex_bin"].isin(sex))
    ]

    dff_mean = (
        dff.groupby(["age", "sex_bin"], as_index=False)[metric]
        .mean()
        .sort_values("age")
    )


    fig = go.Figure()

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
        title=f"{METRIC_TO_TITLE[metric]} vs Age (Level {slice})",
        xaxis_title="Age (years)",
        yaxis_title=METRIC_TO_AXIS[metric]
    )

    return fig


def plot_spinal_profile(df, metric, age, sex):
    # compute mean per slice and sex
    dff = df[(df["age"] == age) & df["sex_bin"].isin(sex)]
    dff_mean = (
        dff.groupby(["Slice (I->S)", "sex_bin"], as_index=False)[metric]
        .mean()
        .sort_values("Slice (I->S)")
    )


    fig = go.Figure()

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

    fig.update_layout(
        title=f"{METRIC_TO_TITLE[metric]} vs Slice (Age {age})",
        xaxis_title="Slice",
        yaxis_title=METRIC_TO_AXIS[metric]
    )

    return fig