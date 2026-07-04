"""
This script contains the callback functions used to update the interactive plots,
according to the UI inputs (metric, age, slice, sex)
"""

from dash import Input, Output, html
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go


from plots import plot_age_profile, plot_spinal_profile, plot_heatmap
from config.metrics import METRIC_CONFIG
from config.demographics import SEX_MAP, AGE_DECADE_MAP
from config.metrics import RAW_TO_MODEL_KEY  



def register_callbacks(app, metrics_df, dem_df, centile_curves, slice_vert_map):
    # HEATMAP
    # Plotting the heatmap according to the chosen parameters
    @app.callback(
        Output("heatmap", "figure"),
        Input("metric", "value"),
        Input("sex-heatmap", "value")
    )
    def update_heatmap(metric, sex):
        model_key = RAW_TO_MODEL_KEY.get(metric)
        curves = centile_curves.get(model_key)
        if curves is None:
            return go.Figure().add_annotation(text=f"No centile curves for '{metric}'", showarrow=False)
        return plot_heatmap(curves, metrics_df, metric, sex)
    
    # Linking the line charts param to those of the clicked heatmap cell
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

        # Find closest slice
        level = min(
            slice_vert_map.keys(),
            key=lambda k: abs(k - slice_id)
        )
        level = slice_vert_map[level]

        return age_range, level
    
    # Linking the sex radio buttons to the sex checkboxes
    @app.callback(
        Output("sex-age", "value"),
        Output("sex-spinal", "value"),
        Input("sex-heatmap", "value"),
    )
    def update_sex(sex):
        
        if sex != "All":
            value= [sex]
        else:
            value = ['Male', 'Female']
        
        return value, value
    
    # AGE PLOT
    # Plotting the age profile according to the chosen parameters
    @app.callback(
        Output("age-plot", "figure"),
        Input("metric", "value"),
        Input("level", "value"),
        Input("sex-age", "value")
    )
    def update_age(metric, level, sex):
        sex_codes = [SEX_MAP[s] for s in sex]
        model_key = RAW_TO_MODEL_KEY.get(metric)
        curves = centile_curves.get(model_key)
        if curves is None:
            return go.Figure().add_annotation(text=f"No centile curves for '{metric}'", showarrow=False)
        return plot_age_profile(curves, metrics_df, metric, level, sex_codes, slice_vert_map)

    # SPINAL PLOT
    # Plotting the spinal profile according to the chosen parameters
    @app.callback(
        Output("spinal-plot", "figure"),
        Input("metric", "value"),
        Input("age", "value"),
        Input("sex-spinal", "value")
    )
    def update_spinal(metric, age, sex):
        sex_codes = [SEX_MAP[s] for s in sex]
        model_key = RAW_TO_MODEL_KEY.get(metric)
        curves = centile_curves.get(model_key)
        if curves is None:
            return go.Figure().add_annotation(text=f"No centile curves for '{metric}'", showarrow=False)
        return plot_spinal_profile(curves, metrics_df, metric, age, sex_codes)

    # Metric thumbnail
    @app.callback(
        Output("metric-info-card", "children"),
        Input("metric", "value"),
    )
    def update_metric_card(metric):
        info = METRIC_CONFIG[metric]
        return html.Div([
            html.Img(src=info["img"],
                     style={"width": "100%", "borderRadius": "8px"}),
        ], style={
            "border": "1px solid #ddd",
            "borderRadius": "10px", #Round corners
            "padding": "12px",
            "backgroundColor": "white",
            "boxShadow": "0 1px 4px rgba(0,0,0,0.08)"
        })