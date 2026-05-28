"""
This script generates the Dash app layout
It:
- Creates a left side bar to select the metric using a dropdown
- Organizes two main visualization panels, and provides controls for selecting controls age/slice and sex
- Connects these elements to callback IDs used for interactive updates
"""

from dash import dcc, html
from config.metrics import METRICS, METRIC_CONFIG
from config.anatomy import MID_VERT_DICT


def create_layout(df):

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
                        {"label": METRIC_CONFIG[m]["title"], "value": m} for m in METRICS
                    ],
                    value=METRICS[0],
                    id="metric"
                ),
                
                html.Div(id="metric-info-card"),

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
