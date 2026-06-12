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

def compute_n(metrics_df, level=None, age=None, sex_codes=None, mode="global"):
    """Callback helper to compute the number of participants in the raw dataset corresponding to the selected subgroup

    Args:
        metrics_df (pd.DataFrame): Contains the raw data
        level (int, optional): Vertebral level of the subgroup. Defaults to None.
        age (list, optional): Age range of the subgroup. Defaults to None.
        sex_codes (list, optional): Sex of the subgroup. Defaults to None.
        mode (str, optional): Targeted plot (age_profile, spinal_profile, global). Defaults to "global".

    Returns:
        int: size of the subgroup
    """
    df = metrics_df.copy()

    if sex_codes is not None:
        df = df[df["sex_bin"].isin(sex_codes)]

    if mode == "age_profile":
        df = df[df["VertLevel"] == level]

    elif mode == "spinal_profile":
        df = df[df["age"].between(age[0], age[1])]

    return df["participant_id"].nunique()


def register_callbacks(app, norm_df, metrics_df):
    
    # HEATMAP
    # Plotting the heatmap according to the chosen parameters
    @app.callback(
        Output("heatmap", "figure"),
        Input("metric", "value"),
        Input("sex-heatmap", "value")
    )
    def update_heatmap(metric, sex):
        
        fig = plot_heatmap(norm_df, metric, sex)

        sex_codes = [SEX_MAP[sex]] if sex != "All" else [0, 1]

        n = compute_n(
            metrics_df,
            sex_codes=sex_codes,
            mode="global"
        )

        fig.update_layout(
            title=f"{fig.layout.title.text}<br><sup>N = {n}</sup>"
        )

        return fig
    
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

        closest_row = (
            norm_df.iloc[
                (norm_df["Slice (I->S)"] - slice_id)
                .abs()
                .argsort()[:1]
            ]
        )

        level = int(closest_row["VertLevel"].iloc[0])

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
        
        fig = plot_age_profile(norm_df, metric, level, sex_codes)
        
        n = compute_n(
            metrics_df,
            level=level,
            sex_codes=sex_codes,
            mode="age_profile"
        )

        fig.update_layout(
            title=f"{fig.layout.title.text}<br><sup>N = {n}</sup>"
        )

        return fig

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
        
        fig = plot_spinal_profile(norm_df, metric, age, sex_codes)
        
        n = compute_n(
            metrics_df,
            age=age,
            sex_codes=sex_codes,
            mode="spinal_profile"
        )

        fig.update_layout(
            title=f"{fig.layout.title.text}<br><sup>N = {n}</sup>"
        )

        return fig    
    
    # THUMBNAILS
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
