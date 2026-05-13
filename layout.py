from dash import dcc, html

METRIC_TO_TITLE = {
    'MEAN(diameter_AP)': 'AP Diameter',
    'MEAN(area)': 'Cross-Sectional Area',
    'MEAN(diameter_RL)': 'Transverse Diameter',
    'MEAN(eccentricity)': 'Eccentricity',
    'MEAN(solidity)': 'Solidity',
}

def create_layout(df):

    metrics = [col for col in df.columns if "MEAN" in col]

    return html.Div([

        html.H1(
            children="Spinal Cord Normative Chart",
            style={'textAlign': 'center'}
        ),

        # Main layout
        html.Div([

            # LEFT
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

                    html.H3("Age Plot Controls"),

                    html.Label('Slice'),
                    dcc.Slider(
                        min=df["Slice (I->S)"].min(),
                        max=df["Slice (I->S)"].max(),
                        step=50,
                        value=int(df["Slice (I->S)"].median()),
                        id="slice"
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

                    html.H3("Spinal Plot Controls"),

                    html.Label('Age'),
                    dcc.Slider(
                        min=df["age"].min(),
                        max=df["age"].max(),
                        step=1,
                        value=int(df["age"].median()),
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
