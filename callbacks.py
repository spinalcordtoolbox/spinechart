"""
This script contains the callback functions used to update the interactive plots:
- age profile
- spinal profile
according to the UI inputs (metric, age, slice, sex)
"""

from dash import Input, Output

from plots import plot_age_profile, plot_spinal_profile

SEX_MAP = {"Male": 0, "Female": 1}


def register_callbacks(app, df):

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
