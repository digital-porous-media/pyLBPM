"""Pre-Simulation analysis page.

Displays morphological drainage results (morphdrain.csv) and a geometry
slice viewer loaded from the simulation directory.
"""

import base64

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.express as px
from dash import Input, Output, State, callback, dcc, html

from pyLBPM.dashboard import dataloader, ids

dash.register_page(__name__, name="Pre-Simulation", order=1)

sim_dir = dataloader.get_sim_dir()


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
        html.H1("Pre-Simulation Analysis"),
        html.Hr(),
        dbc.Alert(
            "Morphological drainage analysis characterizes pore-scale invasion patterns before "
            "running the full simulation. Results are read from morphdrain.csv in the simulation directory.",
            color="info",
        ),

        html.Div(id="presim-status", className="mb-3"),

        html.Hr(),

        # Main content: slice + chart side by side
        dbc.Row([
            # Geometry slice viewer
            dbc.Col([
                html.H5("Geometry Slice"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Axis"),
                        dbc.Select(
                            id=ids.PRESIM_SLICE_AXIS,
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
                        dcc.Slider(
                            id=ids.PRESIM_SLICE_INDEX,
                            min=0, max=1, step=1, value=0, marks=None,
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                    ], width=8),
                ], className="mb-2"),
                dcc.Graph(
                    id=ids.IMAGE_SLICE,
                    figure=_empty_fig("Loading geometry…"),
                    style={"height": "380px"},
                ),
                dcc.Store(id=ids.PRESIM_GEOMETRY_STORE),
            ], width=6),

            # Morphdrain chart
            dbc.Col([
                html.H5("Drainage Analysis"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("X axis"),
                        dbc.Select(id=ids.PRESIM_X_COL, value=""),
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Y axis"),
                        dbc.Select(id=ids.PRESIM_Y_COL, value=""),
                    ], width=6),
                ], className="mb-2"),
                dcc.Graph(
                    id=ids.MORPHDRAIN_LINE_CHART,
                    figure=_empty_fig("Loading morphdrain.csv…"),
                    style={"height": "380px"},
                ),
                dcc.Store(id=ids.PRESIM_CSV_STORE),
            ], width=6),
        ]),

        # Hidden trigger to load data on page load
        dcc.Location(id="presim-location", refresh=False),
    ],
)


@callback(
    Output("presim-status", "children"),
    Output(ids.PRESIM_CSV_STORE, "data"),
    Output(ids.PRESIM_X_COL, "options"),
    Output(ids.PRESIM_X_COL, "value"),
    Output(ids.PRESIM_Y_COL, "options"),
    Output(ids.PRESIM_Y_COL, "value"),
    Output(ids.PRESIM_GEOMETRY_STORE, "data"),
    Output(ids.PRESIM_SLICE_INDEX, "max"),
    Output(ids.PRESIM_SLICE_INDEX, "value"),
    Input("presim-location", "pathname"),
)
def load_data(_pathname):
    """Load morphdrain.csv and geometry .raw on page load."""
    import io
    import posixpath

    import pandas as pd

    from pyLBPM.filesystem import get_filesystem

    fs = get_filesystem()
    errors = []
    csv_data = None
    cols = []
    x_val = y_val = ""
    geo_store = None
    slice_max = 1
    slice_val = 0

    sim_dir_str = str(sim_dir).replace("\\", "/")

    # Load morphdrain.csv
    csv_path = posixpath.join(sim_dir_str.rstrip("/"), "morphdrain.csv")
    try:
        raw_csv = fs.read_file(csv_path).decode("utf-8")
        df = pd.read_csv(io.StringIO(raw_csv), sep=r"\s+")
        csv_data = df.to_dict("records")
        cols = [{"label": c, "value": c} for c in df.columns]
        x_val = df.columns[0]
        y_val = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    except FileNotFoundError:
        errors.append("morphdrain.csv not found.")
    except Exception as e:
        errors.append(f"morphdrain.csv: {e}")

    # Load geometry .morphdrain.raw
    try:
        files = fs.list_dir(sim_dir_str)
        raw_files = [f for f in files if f.endswith(".morphdrain.raw")]
        if raw_files:
            raw_path = posixpath.join(sim_dir_str.rstrip("/"), raw_files[0])
            raw_bytes = fs.read_file(raw_path)
            geo_store = {"b64": base64.b64encode(raw_bytes).decode(), "filename": raw_files[0]}
            n3 = len(raw_bytes)
            n = round(n3 ** (1 / 3))
            if n ** 3 == n3:
                geo_store["nx"] = geo_store["ny"] = geo_store["nz"] = n
                slice_max = n - 1
                slice_val = n // 2
        else:
            errors.append("No *.morphdrain.raw file found.")
    except Exception as e:
        errors.append(f"Geometry: {e}")

    if errors:
        status = dbc.Alert([html.B("Some files could not be loaded. "), " | ".join(errors)],
                           color="warning")
    else:
        status = dbc.Alert("Pre-simulation data loaded successfully.", color="success")

    return status, csv_data, cols, x_val, cols, y_val, geo_store, slice_max, slice_val


@callback(
    Output(ids.MORPHDRAIN_LINE_CHART, "figure"),
    Input(ids.PRESIM_X_COL, "value"),
    Input(ids.PRESIM_Y_COL, "value"),
    State(ids.PRESIM_CSV_STORE, "data"),
    prevent_initial_call=True,
)
def update_chart(x_col, y_col, records):
    if not records or not x_col or not y_col:
        return _empty_fig("Select columns to plot")
    import pandas as pd
    df = pd.DataFrame(records)
    fig = px.line(df, x=x_col, y=y_col,
                  title=f"{y_col} vs {x_col}",
                  labels={x_col: x_col, y_col: y_col})
    fig.update_layout(margin=dict(l=40, r=10, t=40, b=30))
    return fig


@callback(
    Output(ids.IMAGE_SLICE, "figure"),
    Input(ids.PRESIM_SLICE_AXIS, "value"),
    Input(ids.PRESIM_SLICE_INDEX, "value"),
    State(ids.PRESIM_GEOMETRY_STORE, "data"),
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
