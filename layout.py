"""
This script generates the Dash app layout
It:
- Creates a left side bar to select the metric using a dropdown
- Organizes two main visualization panels, and provides controls for selecting controls age/slice and sex
- Connects these elements to callback IDs used for interactive updates
"""

from dash import dcc, html
from config.metrics import METRICS, METRIC_CONFIG
from config.anatomy import VERT_DICT
from plots import plot_age_profile, plot_spinal_profile, plot_heatmap, plot_age_boxplot


def create_layout(metrics_df, dem_df):

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

                dcc.Tabs([

                    # NORMATIVE TAB
                    dcc.Tab(label="Normative Charts", children=[

                        # HEATMAP
                        html.Div([

                            html.H3("Heatmap"),

                            html.Label("Sex"),

                            dcc.RadioItems(
                                options=["All", "Male", "Female"],
                                value="All",
                                id="sex-heatmap",
                                inline=True
                            ),

                            dcc.Graph(id="heatmap")

                        ], style={
                            'padding': '20px',
                            'borderBottom': '1px solid #ccc'
                        }),

                        # AGE PLOT
                        html.Div([

                            html.H3("Age Plot"),

                            html.Label('Vertebral level'),
                            html.Div(
                                dcc.Slider(
                                    min=metrics_df["VertLevel"].min(),
                                    max=metrics_df["VertLevel"].max(),
                                    step=1,
                                    value=int(metrics_df["VertLevel"].median()),
                                    marks=VERT_DICT,
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
                                min=metrics_df["age"].min(),
                                max=metrics_df["age"].max(),
                                step=1,
                                value=[
                                    int(metrics_df["age"].median()),
                                    int(metrics_df["age"].median()) + 1
                                ],
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
                        }),

                    ]),

                    # DEMOGRAPHICS TAB
                    dcc.Tab(label="Demographics", children=[

                        html.Div([

                            html.H3("Age Distribution by Dataset"),

                            dcc.Graph(
                                figure=plot_age_boxplot(dem_df),                        
                                id="age-boxplot",
                                style={"height": "600px"}
                            )

                        ], style={'padding': '20px'}),

                    ])

                ])

            ], style={
                'width': '78%',
                'display': 'inline-block',
                'verticalAlign': 'top'
            })
            
    ], style={
        'display': 'flex'
    })

])