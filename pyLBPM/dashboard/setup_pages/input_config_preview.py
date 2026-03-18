"""Input Configuration Preview page.

Displays the current input.db file from the simulation directory with
syntax highlighting and a manual-edit fallback.
"""

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from pyLBPM.dashboard import ids

dash.register_page(__name__, name="Review Input Configuration", order=1, path="/input-config")

layout = dbc.Container(
    fluid=True,
    children=[
        html.H1("Review Input Configuration"),
        html.Hr(),
        dbc.Row([
            dbc.Col([
                dbc.Label("Simulation directory path"),
                dbc.Input(
                    id="config-sim-dir",
                    type="text",
                    placeholder="/path/to/simulation/directory",
                ),
            ], width=8),
            dbc.Col([
                dbc.Label("\u00a0"),
                dbc.Button("Load input.db", id="config-load-btn",
                           color="primary", className="d-block"),
            ], width=2),
            dbc.Col([
                dbc.Label("\u00a0"),
                dbc.Button("Edit", id="config-edit-btn",
                           color="light", className="d-block", disabled=True),
            ], width=2),
        ], className="mb-3"),

        html.Div(id="config-status"),
        html.Hr(),

        # Read-only markdown display (hidden while editing)
        html.Div(
            id="config-display",
            children=html.P("Load a simulation directory to view input.db.",
                            className="text-muted"),
        ),

        # Edit panel (replaces display while editing)
        html.Div(id="config-edit-panel", style={"display": "none"}, children=[
            dbc.Textarea(
                id="config-edit-textarea",
                style={"height": "500px", "fontFamily": "monospace", "fontSize": "13px"},
            ),
            dbc.Row([
                dbc.Col([
                    dbc.Button("Save changes", id="config-save-btn",
                               color="success", className="me-2"),
                    dbc.Button("Cancel", id="config-cancel-btn", color="secondary"),
                ], className="mt-2"),
            ]),
            html.Div(id="config-save-status", className="mt-2"),
        ]),

        # Store for current raw text
        dcc.Store(id="config-store"),
    ],
)


@callback(
    Output("config-display", "children"),
    Output("config-store", "data"),
    Output("config-status", "children"),
    Output("config-edit-btn", "disabled"),
    Input("config-load-btn", "n_clicks"),
    State("config-sim-dir", "value"),
    prevent_initial_call=True,
)
def load_config(n_clicks, sim_dir):
    if not sim_dir:
        return (
            html.P("Enter a simulation directory path.", className="text-muted"),
            None,
            dbc.Alert("Please enter a path.", color="warning"),
            True,
        )
    import posixpath
    db_path = posixpath.join(sim_dir.rstrip("/"), "input.db")
    try:
        from pyLBPM.filesystem import get_filesystem
        fs = get_filesystem()
        raw = fs.read_file(db_path).decode("utf-8")
        display = dcc.Markdown(f"```\n{raw}\n```",
                               style={"fontFamily": "monospace", "fontSize": "13px"})
        return display, raw, dbc.Alert(f"Loaded: {db_path}", color="success"), False
    except FileNotFoundError:
        return (
            html.P("input.db not found.", className="text-muted"),
            None,
            dbc.Alert(f"File not found: {db_path}", color="danger"),
            True,
        )
    except Exception as e:
        return (
            html.P(str(e), className="text-danger"),
            None,
            dbc.Alert(f"Error: {e}", color="danger"),
            True,
        )


@callback(
    Output("config-edit-panel", "style", allow_duplicate=True),
    Output("config-display", "style", allow_duplicate=True),
    Output("config-edit-textarea", "value"),
    Input("config-edit-btn", "n_clicks"),
    Input("config-cancel-btn", "n_clicks"),
    State("config-store", "data"),
    prevent_initial_call=True,
)
def toggle_edit(edit_clicks, cancel_clicks, stored_text):
    triggered = dash.callback_context.triggered[0]["prop_id"]
    if "config-cancel-btn" in triggered:
        return {"display": "none"}, {}, ""
    return {}, {"display": "none"}, stored_text or ""


@callback(
    Output("config-save-status", "children"),
    Output("config-store", "data", allow_duplicate=True),
    Output("config-display", "children", allow_duplicate=True),
    Output("config-edit-panel", "style", allow_duplicate=True),
    Output("config-display", "style", allow_duplicate=True),
    Input("config-save-btn", "n_clicks"),
    State("config-edit-textarea", "value"),
    State("config-sim-dir", "value"),
    prevent_initial_call=True,
)
def save_config(n_clicks, text, sim_dir):
    if not sim_dir or not text:
        return dbc.Alert("Nothing to save.", color="warning"), dash.no_update, dash.no_update, dash.no_update, dash.no_update
    import posixpath
    db_path = posixpath.join(sim_dir.rstrip("/"), "input.db")
    try:
        from pyLBPM.filesystem import get_filesystem
        fs = get_filesystem()
        fs.write_file(db_path, text.encode("utf-8"))
        display = dcc.Markdown(f"```\n{text}\n```",
                               style={"fontFamily": "monospace", "fontSize": "13px"})
        return dbc.Alert("Saved successfully.", color="success"), text, display, {"display": "none"}, {}
    except Exception as e:
        return dbc.Alert(f"Save failed: {e}", color="danger"), dash.no_update, dash.no_update, dash.no_update, dash.no_update
