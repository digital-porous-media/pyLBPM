"""Subphase Analysis page for the analysis dashboard.

Displays subphase.csv data with interactive charting.
"""

import pandas as pd
import plotly.express as px
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from pyLBPM.dashboard import dataloader, ids, script_export

dash.register_page(__name__, name="Subphase Analysis", order=3)

sim_dir = dataloader.get_sim_dir()

layout = dbc.Container(
    fluid=True,
    style={"marginTop": "20px"},
    children=[
        # Header row with title and Load button
        dbc.Row([
            dbc.Col([html.H1("Subphase Analysis")], xs=9),
            dbc.Col([
                dbc.Button("Load Latest Results", id=ids.SUBPHASE_REFRESH_BTN, color="success",
                           size="sm", className="w-100"),
            ], xs=3),
        ], className="mb-2", align="center"),
        html.Hr(),

        # Real-time polling interval
        dcc.Interval(id=ids.SUBPHASE_INTERVAL, interval=60000, disabled=False),

        # Controls card
        dbc.Card(
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("X-axis:"),
                        dcc.Dropdown(
                            id=ids.SUBPHASE_X_VAR,
                            options=[],
                            value=None,
                        ),
                    ], xs=6),
                    dbc.Col([
                        dbc.Label("Y-axis (select one or more):"),
                        dcc.Dropdown(
                            id=ids.SUBPHASE_Y_VAR,
                            options=[],
                            value=[],
                            multi=True,
                        ),
                    ], xs=6),
                ], align="end"),
                html.Div(id="subphase-status", className="mt-2"),
            ]),
            className="mb-3",
        ),

        # Export button on its own row
        dbc.Row([
            dbc.Col([
                dbc.Button("Export Visualization Script", id=ids.SUBPHASE_EXPORT_BTN, color="outline-primary",
                           size="sm"),
            ], xs=3),
        ], className="mb-2"),

        # Chart container
        dbc.Card(
            dbc.CardBody([
                dcc.Loading(
                    children=[
                        html.Div(id="subphase-chart-container", children=dcc.Graph(id="subphase-chart"))
                    ],
                    type="default",
                ),
            ]),
            className="mb-3",
        ),

        # Store for CSV data
        dcc.Store(id=ids.SUBPHASE_CSV_STORE),

        # Download component and modal for export
        dcc.Download(id=ids.SUBPHASE_DOWNLOAD),
        dbc.Modal([
            dbc.ModalHeader("Export Subphase Script"),
            dbc.ModalBody([
                dbc.Label("Backend:"),
                dbc.RadioItems(
                    id=ids.SUBPHASE_EXPORT_BACKEND,
                    options=[
                        {"label": "Matplotlib", "value": "matplotlib"},
                        {"label": "Plotly", "value": "plotly"},
                    ],
                    value="matplotlib",
                    inline=True,
                    className="mb-3",
                ),
                dbc.Label("Filename:"),
                dbc.Input(id=ids.SUBPHASE_EXPORT_FILENAME, value="subphase_plot.py", type="text"),
            ]),
            dbc.ModalFooter([
                dbc.Button("Save", id=ids.SUBPHASE_EXPORT_CONFIRM, color="primary"),
                dbc.Button("Cancel", id=ids.SUBPHASE_EXPORT_CANCEL, color="secondary"),
            ]),
        ], id=ids.SUBPHASE_EXPORT_MODAL),

        # Trigger load on page visit
        dcc.Location(id="subphase-location", refresh=False),
    ],
)


@callback(
    Output(ids.SUBPHASE_CSV_STORE, "data"),
    Output(ids.SUBPHASE_X_VAR, "options"),
    Output(ids.SUBPHASE_Y_VAR, "options"),
    Output("subphase-status", "children"),
    Input("subphase-location", "pathname"),
    Input(ids.SUBPHASE_INTERVAL, "n_intervals"),
    Input(ids.SUBPHASE_REFRESH_BTN, "n_clicks"),
)
def load_data(_pathname, _intervals, _refresh):
    """Load subphase.csv from filesystem and populate dropdowns."""
    from pyLBPM.filesystem import get_filesystem

    sim_dir_str = str(sim_dir).replace("\\", "/")
    csv_path = f"{sim_dir_str}/subphase.csv"

    try:
        fs = get_filesystem()
        csv_bytes = fs.read_file(csv_path)
        csv_text = csv_bytes.decode("utf-8")

        # Parse CSV (space-delimited)
        df = pd.read_csv(pd.io.common.StringIO(csv_text), sep=r"\s+")

        # Add a synthetic step column (sequential index)
        df["sim.step"] = range(len(df))

        col_options = [{"label": col, "value": col} for col in df.columns]

        return (
            df.to_dict("records"),
            col_options,
            col_options,
            dbc.Alert(f"Loaded subphase.csv", color="success"),
        )
    except FileNotFoundError:
        return (
            None,
            [],
            [],
            dbc.Alert(
                f"subphase.csv not found in {csv_path}",
                color="danger",
            ),
        )
    except Exception as e:
        return (
            None,
            [],
            [],
            dbc.Alert(f"Error loading subphase.csv: {e}", color="danger"),
        )


@callback(
    Output("subphase-chart", "figure"),
    Input(ids.SUBPHASE_X_VAR, "value"),
    Input(ids.SUBPHASE_Y_VAR, "value"),
    Input(ids.SUBPHASE_CSV_STORE, "data"),
)
def update_chart(x_var, y_vars, csv_data):
    """Update chart when dropdown selections change or CSV data updates."""
    if not csv_data or not x_var or not y_vars:
        return px.line(title="Select both X and Y axes")

    df = pd.DataFrame(csv_data)
    try:
        fig = px.line(df, x=x_var, y=y_vars, template="plotly_white")
        y_label = ", ".join(y_vars) if isinstance(y_vars, list) else y_vars
        fig.update_layout(title=f"{y_label} vs {x_var}")
        return fig
    except Exception as e:
        return px.line(title=f"Error: {e}")


@callback(
    Output(ids.SUBPHASE_EXPORT_MODAL, "is_open"),
    Input(ids.SUBPHASE_EXPORT_BTN, "n_clicks"),
    Input(ids.SUBPHASE_EXPORT_CONFIRM, "n_clicks"),
    Input(ids.SUBPHASE_EXPORT_CANCEL, "n_clicks"),
    State(ids.SUBPHASE_EXPORT_MODAL, "is_open"),
    prevent_initial_call=True,
)
def toggle_export_modal(export_clicks, confirm_clicks, cancel_clicks, is_open):
    """Toggle export modal visibility."""
    if export_clicks or cancel_clicks:
        return not is_open
    return is_open


@callback(
    Output(ids.SUBPHASE_DOWNLOAD, "data"),
    Input(ids.SUBPHASE_EXPORT_CONFIRM, "n_clicks"),
    State(ids.SUBPHASE_X_VAR, "value"),
    State(ids.SUBPHASE_Y_VAR, "value"),
    State(ids.SUBPHASE_EXPORT_FILENAME, "value"),
    State(ids.SUBPHASE_EXPORT_BACKEND, "value"),
    prevent_initial_call=True,
)
def generate_script(n_clicks, x_var, y_vars, filename, backend):
    """Generate and download the subphase script."""
    if not n_clicks or not x_var or not y_vars or not filename:
        return None

    if backend == "matplotlib":
        script_content = script_export.subphase_script_matplotlib(str(sim_dir), x_var, y_vars)
    else:
        script_content = script_export.subphase_script(str(sim_dir), x_var, y_vars)

    return dict(content=script_content, filename=filename)
