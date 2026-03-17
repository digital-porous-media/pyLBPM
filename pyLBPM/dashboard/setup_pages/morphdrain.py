"""Morphological Pre-Analysis page.

Displays morphological drainage results (morphdrain.csv) and a geometry
slice image. Provides a button to trigger a morphological drainage run.
"""

import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import numpy as np
import base64
from dash import Input, Output, State, callback, dcc, html

dash.register_page(__name__, name="Morphological Pre-Analysis", order=2, path="/morphdrain")


def _empty_fig(msg="No data"):
    import plotly.graph_objects as go
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper",
                       x=0.5, y=0.5, showarrow=False, font=dict(size=14))
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    return fig


layout = dbc.Container(
    fluid=True,
    children=[
        html.H1("Morphological Pre-Analysis"),
        html.Hr(),
        dbc.Alert(
            "Morphological drainage analysis characterizes pore-scale invasion patterns before "
            "running the full simulation. Results are stored as morphdrain.csv.",
            color="info",
        ),

        # Controls
        dbc.Row([
            dbc.Col([
                dbc.Label("Simulation directory"),
                dbc.Input(id="morphdrain-sim-dir", type="text",
                          placeholder="/path/to/simulation/directory"),
            ], width=7),
            dbc.Col([
                dbc.Label("\u00a0"),
                dbc.Button("Load Results", id="morphdrain-load-btn",
                           color="primary", className="me-2"),
                dbc.Button("Run Morphological Drainage", id="morphdrain-run-btn",
                           color="warning"),
            ], width=5),
        ], className="mb-2"),

        # Run status / load status
        html.Div(id="morphdrain-status", className="mb-3"),
        dcc.Interval(id="morphdrain-poll-interval", interval=3000, disabled=True),
        dcc.Store(id="morphdrain-run-store", data={"running": False}),

        html.Hr(),

        # Main content: slice + chart side by side
        dbc.Row([
            # Slice viewer
            dbc.Col([
                html.H5("Geometry Slice"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Axis"),
                        dbc.Select(
                            id="morphdrain-slice-axis",
                            options=[
                                {"label": "X (dim 0)", "value": "0"},
                                {"label": "Y (dim 1)", "value": "1"},
                                {"label": "Z (dim 2, fastest)", "value": "2"},
                            ],
                            value="2",
                        ),
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Slice index"),
                        dcc.Slider(id="morphdrain-slice-index", min=0, max=1,
                                   step=1, value=0, marks=None,
                                   tooltip={"placement": "bottom", "always_visible": True}),
                    ], width=8),
                ], className="mb-2"),
                dcc.Graph(id="morphdrain-slice-graph", figure=_empty_fig("Load a simulation directory"),
                          style={"height": "380px"}),
                dcc.Store(id="morphdrain-geo-store"),
            ], width=6),

            # Morphdrain chart
            dbc.Col([
                html.H5("Drainage Analysis"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("X axis"),
                        dbc.Select(id="morphdrain-x-col", value=""),
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Y axis"),
                        dbc.Select(id="morphdrain-y-col", value=""),
                    ], width=6),
                ], className="mb-2"),
                dcc.Graph(id="morphdrain-line-chart",
                          figure=_empty_fig("Load morphdrain.csv"),
                          style={"height": "380px"}),
                dcc.Store(id="morphdrain-data-store"),
            ], width=6),
        ]),
    ],
)


@callback(
    Output("morphdrain-status", "children"),
    Output("morphdrain-data-store", "data"),
    Output("morphdrain-x-col", "options"),
    Output("morphdrain-x-col", "value"),
    Output("morphdrain-y-col", "options"),
    Output("morphdrain-y-col", "value"),
    Output("morphdrain-geo-store", "data"),
    Output("morphdrain-slice-index", "max"),
    Output("morphdrain-slice-index", "value"),
    Input("morphdrain-load-btn", "n_clicks"),
    State("morphdrain-sim-dir", "value"),
    prevent_initial_call=True,
)
def load_morphdrain(n_clicks, sim_dir):
    if not sim_dir:
        return dbc.Alert("Enter a simulation directory.", color="warning"), \
               None, [], "", [], "", None, 1, 0

    import posixpath
    from pyLBPM.filesystem import get_filesystem
    fs = get_filesystem()
    errors = []
    csv_data = None
    cols = []
    x_val = y_val = ""
    geo_store = None
    slice_max = 1
    slice_val = 0

    # Load morphdrain.csv
    csv_path = posixpath.join(sim_dir.rstrip("/"), "morphdrain.csv")
    try:
        raw_csv = fs.read_file(csv_path).decode("utf-8")
        import io
        df = pd.read_csv(io.StringIO(raw_csv), sep=r"\s+")
        csv_data = df.to_dict("records")
        cols = [{"label": c, "value": c} for c in df.columns]
        x_val = df.columns[0]
        y_val = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    except FileNotFoundError:
        errors.append("morphdrain.csv not found.")
    except Exception as e:
        errors.append(f"morphdrain.csv: {e}")

    # Load geometry .morphdrain.raw (look for any *.morphdrain.raw)
    try:
        files = fs.list_dir(sim_dir)
        raw_files = [f for f in files if f.endswith(".morphdrain.raw")]
        if raw_files:
            raw_path = posixpath.join(sim_dir.rstrip("/"), raw_files[0])
            raw_bytes = fs.read_file(raw_path)
            geo_store = {"b64": base64.b64encode(raw_bytes).decode(), "filename": raw_files[0]}
            # Try to infer size as cube root
            n3 = len(raw_bytes)
            n = round(n3 ** (1/3))
            if n ** 3 == n3:
                geo_store["nx"] = geo_store["ny"] = geo_store["nz"] = n
                slice_max = n - 1
                slice_val = n // 2
        else:
            errors.append("No *.morphdrain.raw file found.")
    except Exception as e:
        errors.append(f"Geometry: {e}")

    if errors:
        status = dbc.Alert([html.B("Partial load. "), " | ".join(errors)], color="warning")
    else:
        status = dbc.Alert("Loaded successfully.", color="success")

    return status, csv_data, cols, x_val, cols, y_val, geo_store, slice_max, slice_val


@callback(
    Output("morphdrain-line-chart", "figure"),
    Input("morphdrain-x-col", "value"),
    Input("morphdrain-y-col", "value"),
    State("morphdrain-data-store", "data"),
    prevent_initial_call=True,
)
def update_chart(x_col, y_col, records):
    if not records or not x_col or not y_col:
        return _empty_fig("Select columns to plot")
    df = pd.DataFrame(records)
    fig = px.line(df, x=x_col, y=y_col,
                  title=f"{y_col} vs {x_col}",
                  labels={x_col: x_col, y_col: y_col})
    fig.update_layout(margin=dict(l=40, r=10, t=40, b=30))
    return fig


@callback(
    Output("morphdrain-slice-graph", "figure"),
    Input("morphdrain-slice-axis", "value"),
    Input("morphdrain-slice-index", "value"),
    State("morphdrain-geo-store", "data"),
    prevent_initial_call=True,
)
def update_slice(axis_str, slice_idx, geo_store):
    if not geo_store or "nx" not in geo_store:
        return _empty_fig("Load geometry to view slices")
    axis = int(axis_str)
    nx = geo_store["nx"]
    ny = geo_store.get("ny", nx)
    nz = geo_store.get("nz", nx)
    raw_bytes = base64.b64decode(geo_store["b64"])
    arr = np.frombuffer(raw_bytes, dtype=np.uint8).reshape(nx, ny, nz)
    axis_labels = ["X (dim 0)", "Y (dim 1)", "Z (dim 2, fastest)"]
    if axis == 0:
        s = arr[slice_idx, :, :]
        xl, yl = "Y", "Z"
    elif axis == 1:
        s = arr[:, slice_idx, :]
        xl, yl = "X", "Z"
    else:
        s = arr[:, :, slice_idx]
        xl, yl = "X", "Y"
    fig = px.imshow(s, color_continuous_scale="gray",
                    labels={"x": xl, "y": yl, "color": "label"},
                    title=f"Slice along {axis_labels[axis]} = {slice_idx}",
                    aspect="equal")
    fig.update_layout(margin=dict(l=40, r=10, t=40, b=30))
    return fig


@callback(
    Output("morphdrain-run-store", "data"),
    Output("morphdrain-poll-interval", "disabled"),
    Output("morphdrain-status", "children", allow_duplicate=True),
    Input("morphdrain-run-btn", "n_clicks"),
    State("morphdrain-sim-dir", "value"),
    prevent_initial_call=True,
)
def trigger_morphdrain(n_clicks, sim_dir):
    if not sim_dir:
        return {"running": False}, True, dbc.Alert("Enter a simulation directory.", color="warning")
    # Placeholder: actual HPC job submission to be implemented with Tapis/SFTP
    return (
        {"running": True, "sim_dir": sim_dir},
        False,
        dbc.Alert(
            "Morphological drainage run triggered. "
            "Check your HPC job scheduler for status. "
            "(Direct job submission via Tapis/SFTP coming soon.)",
            color="info",
        ),
    )
