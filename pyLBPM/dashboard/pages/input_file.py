"""Input Configuration page for the analysis dashboard.

Displays the input.db from the simulation directory with syntax highlighting
and allows manual editing and saving.
"""

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from pyLBPM.dashboard import dataloader, ids

dash.register_page(__name__, path="/", name="Input Configuration", order=0)

sim_dir = dataloader.get_sim_dir()

layout = dbc.Container(
    fluid=True,
    children=[
        html.H1("Input Configuration"),
        html.Hr(),
        dbc.Row([
            dbc.Col([
                dbc.Button("Edit", id=ids.ANALYSIS_INPUT_EDIT_BTN,
                           color="secondary", className="me-2", disabled=True),
                dbc.Button("Save changes", id=ids.ANALYSIS_INPUT_SAVE_BTN,
                           color="success", style={"display": "none"}),
            ], width="auto"),
        ], className="mb-3"),

        html.Div(id=ids.ANALYSIS_INPUT_STATUS),
        html.Hr(),

        # Read-only markdown display
        html.Div(
            id=ids.ANALYSIS_INPUT_DB_CONTENT,
            children=html.P("Loading input.db…", className="text-muted"),
        ),

        # Edit textarea (hidden until Edit is clicked)
        html.Div(id=ids.ANALYSIS_INPUT_EDIT_SECTION, style={"display": "none"}, children=[
            html.H5("Manual Edit"),
            dbc.Textarea(
                id=ids.ANALYSIS_INPUT_TEXTAREA,
                style={"height": "500px", "fontFamily": "monospace", "fontSize": "13px"},
            ),
            dbc.Button("Cancel", id="analysis-input-cancel-btn",
                       color="secondary", className="mt-2"),
        ]),

        # Store for raw text content
        dcc.Store(id=ids.ANALYSIS_INPUT_DB_STORE),

        # Trigger auto-load on page visit
        dcc.Location(id="input-file-location", refresh=False),
    ],
)


@callback(
    Output(ids.ANALYSIS_INPUT_DB_CONTENT, "children"),
    Output(ids.ANALYSIS_INPUT_DB_STORE, "data"),
    Output(ids.ANALYSIS_INPUT_STATUS, "children"),
    Output(ids.ANALYSIS_INPUT_EDIT_BTN, "disabled"),
    Input("input-file-location", "pathname"),
)
def load_config(_pathname):
    import posixpath
    from pyLBPM.filesystem import get_filesystem

    sim_dir_str = str(sim_dir).replace("\\", "/")
    db_path = posixpath.join(sim_dir_str.rstrip("/"), "input.db")
    try:
        fs = get_filesystem()
        raw = fs.read_file(db_path).decode("utf-8")
        display = dcc.Markdown(f"```\n{raw}\n```",
                               style={"fontFamily": "monospace", "fontSize": "13px"})
        return display, raw, dbc.Alert(f"Loaded: {db_path}", color="success"), False
    except FileNotFoundError:
        return (
            html.P("input.db not found in the simulation directory.", className="text-muted"),
            None,
            dbc.Alert(f"File not found: {db_path}", color="danger"),
            True,
        )
    except Exception as e:
        return (
            html.P(str(e), className="text-danger"),
            None,
            dbc.Alert(f"Error loading input.db: {e}", color="danger"),
            True,
        )


@callback(
    Output(ids.ANALYSIS_INPUT_EDIT_SECTION, "style"),
    Output(ids.ANALYSIS_INPUT_TEXTAREA, "value"),
    Output(ids.ANALYSIS_INPUT_SAVE_BTN, "style"),
    Input(ids.ANALYSIS_INPUT_EDIT_BTN, "n_clicks"),
    Input("analysis-input-cancel-btn", "n_clicks"),
    State(ids.ANALYSIS_INPUT_DB_STORE, "data"),
    prevent_initial_call=True,
)
def toggle_edit(_edit, _cancel, stored_text):
    triggered = dash.callback_context.triggered[0]["prop_id"]
    if "cancel" in triggered:
        return {"display": "none"}, "", {"display": "none"}
    return {}, stored_text or "", {}


@callback(
    Output(ids.ANALYSIS_INPUT_STATUS, "children", allow_duplicate=True),
    Output(ids.ANALYSIS_INPUT_DB_STORE, "data", allow_duplicate=True),
    Output(ids.ANALYSIS_INPUT_DB_CONTENT, "children", allow_duplicate=True),
    Input(ids.ANALYSIS_INPUT_SAVE_BTN, "n_clicks"),
    State(ids.ANALYSIS_INPUT_TEXTAREA, "value"),
    prevent_initial_call=True,
)
def save_config(_clicks, text):
    if not text:
        return dbc.Alert("Nothing to save.", color="warning"), dash.no_update, dash.no_update
    import posixpath
    from pyLBPM.filesystem import get_filesystem

    sim_dir_str = str(sim_dir).replace("\\", "/")
    db_path = posixpath.join(sim_dir_str.rstrip("/"), "input.db")
    try:
        fs = get_filesystem()
        fs.write_file(db_path, text.encode("utf-8"))
        display = dcc.Markdown(f"```\n{text}\n```",
                               style={"fontFamily": "monospace", "fontSize": "13px"})
        return dbc.Alert("Saved successfully.", color="success"), text, display
    except Exception as e:
        return dbc.Alert(f"Save failed: {e}", color="danger"), dash.no_update, dash.no_update
