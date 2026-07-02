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
import pandas as pd
from pathlib import Path

from parsing import run_parsing_pipeline
from layout import create_layout
from callbacks import register_callbacks
from config.metrics import METRIC_MODEL_CONFIG

metrics_df, dem_df = run_parsing_pipeline()

# Deriving from the raw data slice_idx to VertLevel mapping
slice_vert_map: dict[int, int] = (
    metrics_df[["Slice (I->S)", "VertLevel"]]
    .drop_duplicates()
    .set_index("Slice (I->S)")["VertLevel"]
    .to_dict()
)

# Load pre-computed centile curves (no R at serve time)
centile_curves: dict[str, pd.DataFrame] = {}
for metric in METRIC_MODEL_CONFIG:
    p = Path(f"output/predictions/centile_curves_{metric}.parquet")
    if p.exists():
        centile_curves[metric] = pd.read_parquet(p)
        print(f"  Centile curves loaded: {metric}  ({len(centile_curves[metric]):,} rows)")
    else:
        print(f"  [WARN] No centile curves for '{metric}' — run run_normative_pipeline.py")

# App
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
)
app.layout = create_layout(metrics_df, dem_df)
register_callbacks(app, metrics_df, dem_df, centile_curves, slice_vert_map)

if __name__ == "__main__":
    app.run(debug=True)