"""
This script contains the callback functions used to update the interactive plots,
according to the UI inputs (metric, age, slice, sex)
"""

from dash import Input, Output, html, State
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import pandas as pd
from io import StringIO


from plots import plot_age_profile, plot_spinal_profile, plot_heatmap
from user_pipeline import save_uploaded_zip, prepare_user_dataset, align_control_cohort, prepare_new_data_for_metric
from gamlss_align import apply_alignment_parameters
from gamlss_utils import load_model
from config.metrics import METRIC_MODEL_CONFIG
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
        
    # Uploading cohort
    @app.callback(
        Output("user-control-cohort", "data"),
        Output("cohort-status", "children"),
        Input("upload-cohort", "contents"),
        State("upload-cohort", "filename"),
        prevent_initial_call=True,
    )
    def upload_control_cohort(contents, filename):
        if contents is None: # Check if a file has been uploaded
            raise PreventUpdate

        dataset_dir = save_uploaded_zip(contents, filename)

        clean_metrics, clean_dem = prepare_user_dataset(dataset_dir)

        return (
            clean_metrics.to_json(date_format="iso", orient="split"),
            html.Span(f"Loaded {len(clean_dem)} subjects.", style={"color": "green"}),
        )
        
    @app.callback(
        Output("user-alignment-parameters", "data"),
        Output("cohort-status", "children", allow_duplicate=True),
        Input("align-cohort", "n_clicks"),
        State("user-control-cohort", "data"),
        prevent_initial_call=True,
    )
    def align_uploaded_cohort(n_clicks, cohort_json):
        if n_clicks is None: # Check if a alignment button has been clicked
            raise PreventUpdate

        if cohort_json is None:
            return None, html.Span("Please upload a cohort first.", style={"color": "red"})

        clean_metrics = pd.read_json(StringIO(cohort_json), orient="split")

        results = align_control_cohort(clean_metrics)

        parameters = {metric: result["parameters"].to_json(orient="split") for metric, result in results.items()}

        return (
            parameters,
            html.Span("Alignment completed.", style={"color": "green"}),
        )
    
    # Upload single patient
    @app.callback(
        Output("user-single-patient", "data"),
        Output("patient-status", "children"),
        Input("upload-patient", "contents"),
        State("upload-patient", "filename"),
        prevent_initial_call=True,
    )
    def upload_patient(contents, filename):
        if contents is None: # Check if a file has been uploaded
            raise PreventUpdate

        dataset_dir = save_uploaded_zip(contents, filename)

        clean_metrics, clean_dem = prepare_user_dataset(dataset_dir)

        return (
            clean_metrics.to_json(orient="split"),
            html.Span("Patient loaded.", style={"color": "green"})
        )
    
    @app.callback(
        Output("user-aligned-patient", "data"),
        Output("patient-status", "children", allow_duplicate=True),
        Input("align-patient", "n_clicks"),
        State("user-single-patient", "data"),
        State("user-alignment-parameters", "data"),
        prevent_initial_call=True,
    )
    def align_patient(n_clicks, patient_json, parameters_json):
        if n_clicks is None: # Check if a alignment button has been clicked
            raise PreventUpdate

        if patient_json is None: # Check if patient data has been uploaded
            return None, html.Span("Upload a patient first.", style={"color": "red"})

        if parameters_json is None: # Check if cohort alignment has been estimated
            return None, html.Span("Estimate cohort alignment first.", style={"color": "red"})

        clean_metrics = pd.read_json(StringIO(patient_json), orient="split")

        aligned = {}
        for metric, cfg in METRIC_MODEL_CONFIG.items():
            metric_df = prepare_new_data_for_metric(clean_metrics, metric)

            fit = load_model(cfg["rds_path"])

            parameters = pd.read_json(StringIO(parameters_json[metric]), orient="split")

            aligned_metric = apply_alignment_parameters(fit, metric_df, parameters)

            aligned[metric] = aligned_metric.to_json(orient="split")

        return (
            aligned,
            html.Span("Patient aligned successfully.", style={"color": "green"}),
        )