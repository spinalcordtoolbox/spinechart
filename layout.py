"""
This script generates the Dash app layout
It:
- Creates a left side bar to select the metric using a dropdown
- Organizes two main visualization panels, and provides controls for selecting controls age/slice and sex
- Connects these elements to callback IDs used for interactive updates
"""

from dash import dcc, html

METRIC_TO_TITLE = {
    'MEAN(diameter_AP)': 'AP Diameter',
    'MEAN(area)': 'Cross-Sectional Area',
    'MEAN(diameter_RL)': 'Transverse Diameter',
    'MEAN(compression_ratio)': 'AP/RL Ratio',
    'MEAN(eccentricity)': 'Eccentricity',
    'MEAN(solidity)': 'Solidity',
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

def create_layout(df):

    metrics = [col for col in df.columns if "MEAN" in col]

    return html.Div([

        # Title
        html.H1(
            children="Spinal Cord Normative Chart",
            style={'textAlign': 'center'}
        ),

        # Main layout
        html.Div([

            # LEFT SIDE BAR
            html.Div([

                html.H3("Metric Selection"),

                html.Label('Metric'),
                dcc.Dropdown(
                    options=[
                        {"label": METRIC_TO_TITLE[m], "value": m}
                        for m in metrics
                    ],
                    value=metrics[0],
                    id="metric"
                ),

            ], style={
                'width': '20%',
                'padding': '20px',
                'borderRight': '1px solid #ccc',
                'display': 'inline-block',
                'verticalAlign': 'top'
            }),

            # RIGHT
            html.Div([

                # AGE PLOT
                html.Div([

                    html.H3("Age Plot"),

                    html.Label('Vertebral level'),
                    html.Div(
                        dcc.Slider(
                            min=df["VertLevel"].min(),
                            max=df["VertLevel"].max(),
                            step=1,
                            value=int(df["VertLevel"].median()),
                            marks=MID_VERT_DICT,
                            id="level",
                        ),
                        className="simple-slider"
                    ),

                    html.Br(),

                    html.Label('Sex'),
                    dcc.Checklist(
                        ['Male', 'Female'],
                        value=['Male', 'Female'],
                        id="sex-age"
                    ),

                    dcc.Graph(id="age-plot")

                ], style={
                    'padding': '20px',
                    'borderBottom': '1px solid #ccc'
                }),

                # SPINAL PLOT
                html.Div([

                    html.H3("Spinal Plot"),

                    html.Label('Age'),
                    dcc.RangeSlider(
                        min=df["age"].min(),
                        max=df["age"].max(),
                        step=1,
                        value=[int(df["age"].median()), int(df["age"].median())+1],
                        id="age"
                    ),

                    html.Br(),

                    html.Label('Sex'),
                    dcc.Checklist(
                        ['Male', 'Female'],
                        value=['Male', 'Female'],
                        id="sex-spinal"
                    ),

                    dcc.Graph(id="spinal-plot")

                ], style={
                    'padding': '20px'
                })

            ], style={
                'width': '78%',
                'display': 'inline-block',
                'verticalAlign': 'top'
            })

        ], style={
            'display': 'flex'
        })

    ])
