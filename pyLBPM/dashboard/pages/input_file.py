"""Input Configuration page for the analysis dashboard.

Displays the input.db from the simulation directory with syntax highlighting.
"""

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, callback, dcc, html, State

from pyLBPM.dashboard import dataloader, ids

dash.register_page(__name__, path="/", name="Input Configuration", order=0)

sim_dir = dataloader.get_sim_dir()

layout = dbc.Container(
    fluid=True,
    style={"marginTop": "20px"},
    children=[
        html.H1("Input Configuration"),
        html.Hr(),
        # Input file name and load button
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label("Input file name:"),
                        dbc.Input(
                            id=ids.VIS_3D_INPUT_PATH,
                            type="text",
                            placeholder="input.db",
                            debounce=True,
                            className="form-control",
                        ),
                    ],
                    xs=10,
                ),
                dbc.Col(
                    [
                        dbc.Button(
                            "Load",
                            id=ids.ANALYSIS_INPUT_LOAD_BTN,
                            color="success",
                            className="mt-4",
                        ),
                    ],
                    xs=2,
                    className="d-flex align-items-end",
                ),
            ],
            className="mb-3",
        ),
        html.Div(id=ids.ANALYSIS_INPUT_STATUS),
        html.Hr(),
        # Read-only markdown display
        html.Div(
            id=ids.ANALYSIS_INPUT_DB_CONTENT,
            children=html.P("Loading input.db…", className="text-muted"),
        ),
        # Store for raw text content
        dcc.Store(id=ids.ANALYSIS_INPUT_DB_STORE),
        # Trigger auto-load on page visit
        dcc.Location(id="input-file-location", refresh=False),
    ],
)


@callback(
    Output(ids.VIS_3D_INPUT_PATH, "value"),
    Input("input-file-location", "pathname"),
    State(ids.APP_INPUT_FILE_PATH, "data"),
)
def set_default_input_path(_pathname, stored_path):
    """Restore previously entered filename, or fall back to default."""
    if stored_path:
        return stored_path
    return "input.db"


@callback(
    Output(ids.APP_INPUT_FILE_PATH, "data"),
    Input(ids.VIS_3D_INPUT_PATH, "value"),
    prevent_initial_call=True,
)
def save_input_path(path):
    """Save the input path to app-level store when user changes it."""
    return path


@callback(
    Output(ids.ANALYSIS_INPUT_DB_CONTENT, "children"),
    Output(ids.ANALYSIS_INPUT_DB_STORE, "data"),
    Output(ids.ANALYSIS_INPUT_STATUS, "children"),
    Input("input-file-location", "pathname"),
    Input(ids.ANALYSIS_INPUT_LOAD_BTN, "n_clicks"),
    State(ids.VIS_3D_INPUT_PATH, "value"),
    State(ids.APP_INPUT_FILE_PATH, "data"),
)
def load_config(_pathname, _load_clicks, input_file_path, stored_path):
    from pyLBPM.filesystem import get_filesystem
    from pathlib import Path

    # Treat input_file_path as a filename, construct full path from sim_dir
    filename = stored_path or input_file_path or "input.db"
    db_path = str(sim_dir / filename)

    try:
        fs = get_filesystem()
        raw = fs.read_file(db_path).decode("utf-8")
        display = dcc.Markdown(
            f"```\n{raw}\n```", style={"fontFamily": "monospace", "fontSize": "13px"}
        )
        return display, raw, dbc.Alert(f"Loaded: {db_path}", color="success")
    except FileNotFoundError:
        return (
            html.P(
                f"File not found: {db_path}. "
                "This dashboard looks for 'input.db' by default, but your input file may have a "
                "different name. Enter the correct filename (and full path) in the field above.",
                className="text-muted",
            ),
            None,
            dbc.Alert(
                f"File not found: {db_path}. "
                "This dashboard looks for 'input.db' by default — update the path above "
                "if your input file has a different name.",
                color="danger",
            ),
        )
    except Exception as e:
        return (
            html.P(str(e), className="text-danger"),
            None,
            dbc.Alert(f"Error loading input.db: {e}", color="danger"),
        )
