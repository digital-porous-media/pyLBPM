"""Monitor Simulations page for the analysis dashboard.

Displays timelog.csv data with interactive charting.
Supports real-time updates during a running simulation via polling.
"""

import pandas as pd
import plotly.express as px
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from pyLBPM.dashboard import dataloader, ids

dash.register_page(__name__, name="Monitor Simulations", order=2)

sim_dir = dataloader.get_sim_dir()

layout = dbc.Container(
    fluid=True,
    style={"marginTop": "20px"},
    children=[
        html.H1(id="monitor-heading", children="Timelog Monitoring"),
        html.Hr(),

        # Real-time polling interval
        dcc.Interval(id=ids.MONITOR_INTERVAL, interval=60000, disabled=False),

        # Controls card
        dbc.Card(
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Data file:"),
                        dbc.RadioItems(
                            id=ids.MONITOR_CSV_FILE,
                            options=[
                                {"label": "timelog.csv", "value": "timelog.csv"},
                                {"label": "Permeability.csv", "value": "Permeability.csv"},
                            ],
                            value="timelog.csv",
                            inline=True,
                        ),
                    ], xs=12),
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("X-axis:"),
                        dbc.Select(
                            id=ids.MONITOR_X_VAR,
                            options=[],
                            value=None,
                        ),
                    ], xs=5),
                    dbc.Col([
                        dbc.Label("Y-axis (select one or more):"),
                        dcc.Dropdown(
                            id=ids.MONITOR_Y_VAR,
                            options=[],
                            value=[],
                            multi=True,
                        ),
                    ], xs=5),
                    dbc.Col([
                        dbc.Button("Load Latest Results", id=ids.MONITOR_REFRESH_BTN, color="success",
                                   size="sm", className="w-100"),
                    ], xs=2, className="d-flex align-items-end"),
                ], align="end"),
                html.Div(id="monitor-status", className="mt-2"),
            ]),
            className="mb-3",
        ),

        # Chart container
        dbc.Card(
            dbc.CardBody([
                dcc.Loading(
                    children=[
                        html.Div(id="monitor-chart-container", children=dcc.Graph(id="monitor-chart"))
                    ],
                    type="default",
                ),
            ]),
            className="mb-3",
        ),

        # Store for CSV data
        dcc.Store(id=ids.MONITOR_CSV_STORE),

        # Trigger load on page visit
        dcc.Location(id="monitor-location", refresh=False),
    ],
)


@callback(
    Output(ids.MONITOR_CSV_STORE, "data"),
    Output(ids.MONITOR_X_VAR, "options"),
    Output(ids.MONITOR_Y_VAR, "options"),
    Output("monitor-status", "children"),
    Output("monitor-heading", "children"),
    Input("monitor-location", "pathname"),
    Input(ids.MONITOR_INTERVAL, "n_intervals"),
    Input(ids.MONITOR_REFRESH_BTN, "n_clicks"),
    Input(ids.MONITOR_CSV_FILE, "value"),
)
def load_data(_pathname, _intervals, _refresh, csv_file):
    """Load CSV data from filesystem and populate dropdowns."""
    from pyLBPM.filesystem import get_filesystem

    csv_file = csv_file or "timelog.csv"
    heading = "Single Phase Permeability Monitoring" if csv_file == "Permeability.csv" else "Timelog Monitoring"

    sim_dir_str = str(sim_dir).replace("\\", "/")
    csv_path = f"{sim_dir_str}/{csv_file}"

    try:
        fs = get_filesystem()
        csv_bytes = fs.read_file(csv_path)
        csv_text = csv_bytes.decode("utf-8")

        # Parse CSV (space-delimited)
        df = pd.read_csv(pd.io.common.StringIO(csv_text), sep=r"\s+")

        # Add a synthetic step column only for timelog.csv
        if csv_file == "timelog.csv":
            df["sim.step"] = range(len(df))

        col_options = [{"label": col, "value": col} for col in df.columns]

        return (
            df.to_dict("records"),
            col_options,
            col_options,
            dbc.Alert(f"Loaded {csv_file}", color="success"),
            heading,
        )
    except FileNotFoundError:
        return (
            None,
            [],
            [],
            dbc.Alert(
                f"{csv_file} not found in simulation directory",
                color="danger",
            ),
            heading,
        )
    except Exception as e:
        return (
            None,
            [],
            [],
            dbc.Alert(f"Error loading {csv_file}: {e}", color="danger"),
            heading,
        )


@callback(
    Output("monitor-chart", "figure"),
    Input(ids.MONITOR_X_VAR, "value"),
    Input(ids.MONITOR_Y_VAR, "value"),
    Input(ids.MONITOR_CSV_STORE, "data"),
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
