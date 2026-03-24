"""Pre-Simulation analysis page.

Displays morphological drainage results (morphdrain.csv) and a geometry
slice viewer loaded from the simulation directory.
"""

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.express as px
from dash import Input, Output, State, callback, dcc, html

from pyLBPM.dashboard import dataloader, ids, script_export

dash.register_page(__name__, name="Morphological Drainage", order=1)

sim_dir = dataloader.get_sim_dir()


def _empty_fig(msg="No data"):
    import plotly.graph_objects as go

    fig = go.Figure()
    fig.add_annotation(
        text=msg,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14),
    )
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    return fig


layout = dbc.Container(
    fluid=True,
    style={"marginTop": "20px"},
    children=[
        html.H1("Morphological Drainage Analysis"),
        html.Hr(),
        dbc.Alert(
            "Morphological drainage analysis initializes pore-scale invasion patterns before "
            "running the full simulation. Results are read from morphdrain.csv in the simulation directory.",
            color="info",
        ),
        html.Div(id="presim-status", className="mb-3"),
        html.Hr(),
        # Main content: slice + chart side by side
        dbc.Row(
            [
                # Geometry slice viewer
                dbc.Col(
                    [
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    html.H5(
                                                        "Geometry Slice",
                                                        className="mb-3",
                                                    )
                                                ],
                                                width=8,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Button(
                                                        "Export Visualization Script",
                                                        id=ids.PRESIM_EXPORT_BTN,
                                                        color="outline-primary",
                                                        size="sm",
                                                        className="w-100",
                                                    ),
                                                ],
                                                width=4,
                                            ),
                                        ],
                                        align="end",
                                        className="mb-3",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label("Axis"),
                                                    dbc.Select(
                                                        id=ids.PRESIM_SLICE_AXIS,
                                                        options=[
                                                            {
                                                                "label": "X (dim 0)",
                                                                "value": "0",
                                                            },
                                                            {
                                                                "label": "Y (dim 1)",
                                                                "value": "1",
                                                            },
                                                            {
                                                                "label": "Z (dim 2)",
                                                                "value": "2",
                                                            },
                                                        ],
                                                        value="2",
                                                    ),
                                                ],
                                                width=4,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label("Slice index"),
                                                    dcc.Slider(
                                                        id=ids.PRESIM_SLICE_INDEX,
                                                        min=0,
                                                        max=1,
                                                        step=1,
                                                        value=0,
                                                        marks=None,
                                                        tooltip={
                                                            "placement": "bottom",
                                                            "always_visible": True,
                                                        },
                                                    ),
                                                ],
                                                width=8,
                                                style={"paddingBottom": "20px"},
                                            ),
                                        ],
                                        className="mb-4",
                                    ),
                                    dcc.Graph(
                                        id=ids.IMAGE_SLICE,
                                        figure=_empty_fig("Loading geometry…"),
                                        style={"height": "380px"},
                                    ),
                                ]
                            ),
                            className="h-100",
                        ),
                    ],
                    width=6,
                    className="mb-3",
                ),
                # Morphdrain chart
                dbc.Col(
                    [
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5("Drainage Analysis", className="mb-3"),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label("X axis"),
                                                    dbc.Select(
                                                        id=ids.PRESIM_X_COL, value=""
                                                    ),
                                                ],
                                                width=6,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label("Y axis"),
                                                    dbc.Select(
                                                        id=ids.PRESIM_Y_COL, value=""
                                                    ),
                                                ],
                                                width=6,
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    dcc.Graph(
                                        id=ids.MORPHDRAIN_LINE_CHART,
                                        figure=_empty_fig("Loading morphdrain.csv…"),
                                        style={"height": "380px"},
                                    ),
                                    dcc.Store(id=ids.PRESIM_CSV_STORE),
                                ]
                            ),
                            className="h-100",
                        ),
                    ],
                    width=6,
                    className="mb-3",
                ),
            ]
        ),
        # Download component and modal for export
        dcc.Download(id=ids.PRESIM_DOWNLOAD),
        dbc.Modal(
            [
                dbc.ModalHeader("Export Geometry Slice Script"),
                dbc.ModalBody(
                    [
                        dbc.Label("Backend:"),
                        dbc.RadioItems(
                            id=ids.PRESIM_EXPORT_BACKEND,
                            options=[
                                {"label": "Matplotlib", "value": "matplotlib"},
                                {"label": "Plotly", "value": "plotly"},
                            ],
                            value="matplotlib",
                            inline=True,
                            className="mb-3",
                        ),
                        dbc.Label("Filename:"),
                        dbc.Input(
                            id=ids.PRESIM_EXPORT_FILENAME,
                            value="geometry_slice.py",
                            type="text",
                        ),
                    ]
                ),
                dbc.ModalFooter(
                    [
                        dbc.Button(
                            "Save", id=ids.PRESIM_EXPORT_CONFIRM, color="primary"
                        ),
                        dbc.Button(
                            "Cancel", id=ids.PRESIM_EXPORT_CANCEL, color="secondary"
                        ),
                    ]
                ),
            ],
            id=ids.PRESIM_EXPORT_MODAL,
        ),
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
    Output(ids.PRESIM_SLICE_INDEX, "max"),
    Output(ids.PRESIM_SLICE_INDEX, "value"),
    Input("presim-location", "pathname"),
)
def load_data(_pathname):
    """Load morphdrain.csv and verify geometry .raw exists on page load."""
    import io
    import posixpath

    import pandas as pd

    from pyLBPM.filesystem import get_filesystem

    fs = get_filesystem()
    errors = []
    csv_data = None
    cols = []
    x_val = y_val = ""
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

    # Check geometry .morphdrain.raw (just verify existence and infer dimensions)
    try:
        files = fs.list_dir(sim_dir_str)
        raw_files = [f for f in files if f.endswith(".morphdrain.raw")]
        if raw_files:
            raw_path = posixpath.join(sim_dir_str.rstrip("/"), raw_files[0])
            raw_bytes = fs.read_file(raw_path)
            n3 = len(raw_bytes)
            n = round(n3 ** (1 / 3))
            if n**3 == n3:
                slice_max = n - 1
                slice_val = n // 2
            else:
                errors.append(f"Geometry is not cubic: {n3} bytes.")
        else:
            errors.append("No *.morphdrain.raw file found.")
    except Exception as e:
        errors.append(f"Geometry: {e}")

    if errors:
        status = dbc.Alert(
            [html.B("Some files could not be loaded. "), " | ".join(errors)],
            color="warning",
        )
    else:
        status = dbc.Alert("Pre-simulation data loaded successfully.", color="success")

    return status, csv_data, cols, x_val, cols, y_val, slice_max, slice_val


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
    fig = px.line(
        df,
        x=x_col,
        y=y_col,
        title=f"{y_col} vs {x_col}",
        labels={x_col: x_col, y_col: y_col},
    )
    fig.update_layout(margin=dict(l=40, r=10, t=40, b=30))
    return fig


@callback(
    Output(ids.IMAGE_SLICE, "figure"),
    Input(ids.PRESIM_SLICE_AXIS, "value"),
    Input(ids.PRESIM_SLICE_INDEX, "value"),
    prevent_initial_call=True,
)
def update_slice(axis_str, slice_idx):
    """Update geometry slice by reading file directly from filesystem."""
    import posixpath
    from pyLBPM.filesystem import get_filesystem

    try:
        # Find the .morphdrain.raw file
        fs = get_filesystem()
        sim_dir_str = str(sim_dir).replace("\\", "/")
        files = fs.list_dir(sim_dir_str)
        raw_files = [f for f in files if f.endswith(".morphdrain.raw")]

        if not raw_files:
            return _empty_fig("No geometry file found")

        raw_path = posixpath.join(sim_dir_str.rstrip("/"), raw_files[0])
        raw_bytes = fs.read_file(raw_path)

        # Infer dimensions from file size (assume cubic)
        n3 = len(raw_bytes)
        n = round(n3 ** (1 / 3))
        if n**3 != n3:
            return _empty_fig(f"Geometry not cubic: {n3} bytes")

        # Reshape array
        arr = np.frombuffer(raw_bytes, dtype=np.uint8).reshape(n, n, n)
        axis = int(axis_str)

        axis_labels = ["X (dim 0)", "Y (dim 1)", "Z (dim 2)"]
        if axis == 0:
            s = arr[slice_idx, :, :]
            xl, yl = "Y", "Z"
        elif axis == 1:
            s = arr[:, slice_idx, :]
            xl, yl = "X", "Z"
        else:
            s = arr[:, :, slice_idx]
            xl, yl = "X", "Y"

        fig = px.imshow(
            s,
            color_continuous_scale="gray",
            labels={"x": xl, "y": yl, "color": "label"},
            title=f"Slice along {axis_labels[axis]} = {slice_idx}",
            aspect="equal",
        )
        fig.update_layout(margin=dict(l=40, r=10, t=40, b=30))
        return fig
    except Exception as e:
        return _empty_fig(f"Error loading geometry: {e}")


@callback(
    Output(ids.PRESIM_EXPORT_MODAL, "is_open"),
    Input(ids.PRESIM_EXPORT_BTN, "n_clicks"),
    Input(ids.PRESIM_EXPORT_CONFIRM, "n_clicks"),
    Input(ids.PRESIM_EXPORT_CANCEL, "n_clicks"),
    State(ids.PRESIM_EXPORT_MODAL, "is_open"),
    prevent_initial_call=True,
)
def toggle_export_modal(export_clicks, confirm_clicks, cancel_clicks, is_open):
    """Toggle export modal visibility."""
    if export_clicks or cancel_clicks:
        return not is_open
    return is_open


@callback(
    Output(ids.PRESIM_DOWNLOAD, "data"),
    Input(ids.PRESIM_EXPORT_CONFIRM, "n_clicks"),
    State(ids.PRESIM_SLICE_AXIS, "value"),
    State(ids.PRESIM_SLICE_INDEX, "value"),
    State(ids.PRESIM_EXPORT_FILENAME, "value"),
    State(ids.PRESIM_EXPORT_BACKEND, "value"),
    prevent_initial_call=True,
)
def generate_script(n_clicks, axis_str, slice_idx, filename, backend):
    """Generate and download the geometry slice script."""
    if not n_clicks or axis_str is None or slice_idx is None or not filename:
        return None

    # Find the raw file name
    from pyLBPM.filesystem import get_filesystem
    import posixpath

    try:
        fs = get_filesystem()
        sim_dir_str = str(sim_dir).replace("\\", "/")
        files = fs.list_dir(sim_dir_str)
        raw_files = [f for f in files if f.endswith(".morphdrain.raw")]
        raw_file = raw_files[0] if raw_files else "unknown.morphdrain.raw"
    except Exception:
        raw_file = "unknown.morphdrain.raw"

    axis = int(axis_str)

    if backend == "matplotlib":
        script_content = script_export.presimulation_slice_script_matplotlib(
            str(sim_dir), raw_file, axis, slice_idx
        )
    else:
        script_content = script_export.presimulation_slice_script(
            str(sim_dir), raw_file, axis, slice_idx
        )

    return dict(content=script_content, filename=filename)
