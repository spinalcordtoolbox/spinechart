"""
This script contains the callback functions used to update the interactive plots:
- age profile
- spinal profile
according to the UI inputs (metric, age, slice, sex)
"""

from dash import Input, Output
from dash import html
from dash.exceptions import PreventUpdate

from plots import plot_age_profile, plot_spinal_profile, plot_heatmap
from config.metrics import METRIC_CONFIG
from config.demographics import SEX_MAP, AGE_DECADE_MAP

def register_callbacks(app, df):
    
    @app.callback(
        Output("heatmap", "figure"),
        Input("metric", "value"),
        Input("sex-heatmap", "value")
    )
    def update_heatmap(metric, sex):

        return plot_heatmap(df, metric, sex)
    
    @app.callback(
        Output("age", "value"),
        Output("level", "value"),
        Input("heatmap", "clickData")
    )
    def heatmap_click(click_data):
        if click_data is None:
            raise PreventUpdate
        
        age_decade = click_data["points"][0]["y"]
        slice_id = click_data["points"][0]["x"]

        age_range = AGE_DECADE_MAP[age_decade]

        closest_row = (
            df.iloc[
                (df["Slice (I->S)"] - slice_id)
                .abs()
                .argsort()[:1]
            ]
        )

        level = int(closest_row["VertLevel"].iloc[0])

        return age_range, level
    
    @app.callback(
        Output("age-plot", "figure"),
        Input("metric", "value"),
        Input("level", "value"),
        Input("sex-age", "value")
    )
    def update_age(metric, level, sex):

        sex_codes = [SEX_MAP[s] for s in sex]

        return plot_age_profile(df, metric, level, sex_codes)


    @app.callback(
        Output("spinal-plot", "figure"),
        Input("metric", "value"),
        Input("age", "value"),
        Input("sex-spinal", "value")
    )
    def update_spinal(metric, age, sex):

        sex_codes = [SEX_MAP[s] for s in sex]

        return plot_spinal_profile(df, metric, age, sex_codes)
    
    
    @app.callback(
        Output("metric-info-card", "children"),
        Input("metric", "value")
    )
    def update_metric_card(metric):

        info = METRIC_CONFIG[metric]

        return html.Div([
            html.Div([
                html.Img(
                    src=info["img"],
                    style={
                        "width": "100%",
                        "borderRadius": "8px",
                        "marginBottom": "0px"
                    }
                )
            ]),
        ], style={
            "border": "1px solid #ddd",
            "borderRadius": "10px", #Round corners
            "padding": "12px",
            "backgroundColor": "white",
            "boxShadow": "0 1px 4px rgba(0,0,0,0.08)"
        })
