from dash import Dash
from pathlib import Path

from parsing import run_parsing_pipeline
from stats import run_normative
from layout import create_layout
from callbacks import register_callbacks



df = run_parsing_pipeline(Path("./data"))

norm_df = run_normative(df)

app = Dash(__name__)
app.layout = create_layout(norm_df)
register_callbacks(app, norm_df)

if __name__ == '__main__':
    app.run(debug=True)
