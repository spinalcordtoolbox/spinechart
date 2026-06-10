"""
This script launches the Dash app.
It:
- Loads the files from the local directory ./data, and parse them
- Runs the normative pipeline
- Initializes the Dash app
- Sets up the UI layout and interactive callbacks
"""

from dash import Dash
import dash_bootstrap_components as dbc

from parsing import run_parsing_pipeline
from stats import run_normative
from layout import create_layout
from callbacks import register_callbacks



metrics_df, dem_df = run_parsing_pipeline()

norm_df = run_normative(metrics_df)

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP]
    )
app.layout = create_layout(norm_df, dem_df)
register_callbacks(app, norm_df)

if __name__ == '__main__':
    app.run(debug=True)
