from dash import html
import pathlib
from pyLBPM.dashboard import ids, plotter, widgets
import dash_bootstrap_components as dbc
import pandas as pd


def create_presim_layout(simulation_dir: pathlib.Path, data: pd.DataFrame, page_title, class_name="app-div",
                         slice_id="", plot_id="") -> html.Div:
    try:
        slice_layout = plotter.render_slice(simulation_dir, IMAGE_SLICE_ID=slice_id)
    except FileNotFoundError:
        slice_layout = create_filenotfound_layout(page_title, class_name, slice_id)

    try:
        morphdrain_linechart_layout = plotter.render_morphdrain_linechart(data, LINE_CHART_ID=plot_id)
    except FileNotFoundError:
        morphdrain_linechart_layout = create_filenotfound_layout(page_title, class_name, plot_id)

    return html.Div(
        className=class_name,
        children=[
            html.H1(page_title),
            html.Hr(),
            # TODO: Display simulation input parameters
            # html.H3("Simulation Input Parameters"),
            # dbc.Row([
            #     dbc.Col(
            #         [
            #             widgets.render_dropdown(data, id_str=ids.X_VAR_DROPDOWN,
            #                                      heading="Select x-values to plot", multi_selection=False
            #         ]
            #     )
            html.H3("Morphological Drainage"),
            dbc.Row([
                dbc.Col(
                    [
                        slice_layout
                    ],
                    width=6
                ),
                dbc.Col(
                    [
                        morphdrain_linechart_layout
                    ],
                    width=6
                ),
            ])
        ]
    )


def create_linechart_layout(data: pd.DataFrame, page_title, class_name="app-div", plot_id="") -> html.Div:
    return html.Div(
        className=class_name,
        children=[
            html.H1(page_title),
            html.Hr(),
            dbc.Row([
                dbc.Col(
                    [
                        widgets.render_dropdown(data.keys().tolist(), id_str=ids.X_VAR_DROPDOWN,
                                                heading="Select x-values to plot", multi_selection=False,
                                                default_column_id=0)
                    ], width=6
                ),
                dbc.Col(
                    [
                        widgets.render_dropdown(data.keys().tolist(), id_str=ids.Y_VAR_DROPDOWN,
                                                heading="Select y-values to plot", multi_selection=True,
                                                default_column_id=1)
                    ], width=6
                )
            ]),
            dbc.Row([
                dbc.Col([
                    plotter.render_linechart(data, LINE_CHART_ID=plot_id)
                ])
            ])
        ]
    )


def create_3D_vis_layout(simulation_dir: pathlib.Path, timesteps: list[int], dropdown_cats: list[str],
                         subdomains: list[str], page_title, class_name="app-div", plot_id: str = "") -> html.Div:
    return html.Div(
        className=class_name,
        children=[
            html.H1(page_title),
            html.Hr(),
            dbc.Row([
                dbc.Col(
                    [
                        widgets.render_dropdown(dropdown_cats, id_str=ids.X_VAR_DROPDOWN,
                                                heading="Select data key to plot", multi_selection=False, default_column_id=-1)
                    ], width=6
                ),
                dbc.Col(
                    [
                        widgets.render_dropdown(subdomains, id_str=ids.SINGLE_DROPDOWN,
                                                heading="Select subdomains to plot", multi_selection=True)
                    ], width=6
                )
            ]),
            dbc.Row([
                dbc.Col(
                    [
                        plotter.render_3d_vis(simulation_dir=simulation_dir,
                                              timesteps=timesteps,
                                              VTK_VIS_ID=plot_id)
                    ], width=12
                )
            ]),

            dbc.Row([
                dbc.Col(
                    [
                        widgets.render_slider(timesteps,
                                              id_str=ids.SLIDER,
                                              heading="Select timestep to plot")
                    ], width=12
                ),
            ]),
        ]
    )

def create_filenotfound_layout(page_title, class_name: str="app-div", id_str: str="file-not-found") -> html.Div:
    required_files = {
        "Input File": "input.db",
        "Pre-Simulation": "morphdrain.csv and *.morphdrain.raw",
        "Timelog Monitoring": "timelog.csv",
        "SCAL Analysis": "SCAL.csv",
        "Subphase Analysis": "subphase.csv",
        "3D Visualization": "id_t*.raw or vis*/*.h5"
    }


    return html.Div(
        className=class_name,
        children=[
            html.Hr(),
            html.H6("Could not find the files needed to display this page."),
            html.H6(f"This page requires {required_files.get(page_title)}"),
        ],
        id=id_str
    )
