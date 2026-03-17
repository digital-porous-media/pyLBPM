"""Geometry Setup page — the primary pre-simulation configuration page.

Sections:
  1. Load geometry (.raw binary file)
  2. Domain configuration (nproc, subdomain size, BC, label remapping)
  3. Simulation model configuration (Color / Permeability / Morphology)
  4. Create simulation directory on HPC
"""

import base64
import io

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.express as px
from dash import Input, Output, State, callback, dcc, html

from pyLBPM.dashboard import ids

dash.register_page(__name__, name="Geometry Setup", order=0, path="/")

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
layout = dbc.Container(
    fluid=True,
    children=[
        html.H1("Geometry Setup"),
        html.Hr(),

        # ---- Section 1: Load Geometry ----
        dbc.Card(
            className="mb-3",
            children=[
                dbc.CardHeader(html.H4("1. Load Geometry File", className="mb-0")),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Source"),
                            dbc.RadioItems(
                                id=ids.GEOMETRY_SOURCE_RADIO,
                                options=[
                                    {"label": "Remote / local path", "value": "path"},
                                    {"label": "Browser upload", "value": "upload"},
                                ],
                                value="path",
                                inline=True,
                            ),
                        ], width=12),
                    ], className="mb-2"),

                    # Remote path input (shown when source=path)
                    dbc.Row(id="geometry-path-row", children=[
                        dbc.Col([
                            dbc.Label("File path"),
                            dbc.Input(
                                id=ids.GEOMETRY_REMOTE_PATH,
                                type="text",
                                placeholder="/scratch/user/sim/geometry.raw",
                            ),
                        ], width=10),
                    ], className="mb-2"),

                    # Upload widget (shown when source=upload)
                    dbc.Row(id="geometry-upload-row", style={"display": "none"}, children=[
                        dbc.Col([
                            dcc.Upload(
                                id=ids.GEOMETRY_UPLOAD,
                                children=html.Div([
                                    "Drag and drop or ",
                                    html.A("select a .raw file"),
                                    html.Br(),
                                    html.Small("Recommended for files < 500 MB. "
                                               "For larger files use the remote path option.",
                                               className="text-muted"),
                                ]),
                                style={
                                    "width": "100%", "height": "80px", "lineHeight": "40px",
                                    "borderWidth": "1px", "borderStyle": "dashed",
                                    "borderRadius": "5px", "textAlign": "center",
                                },
                                max_size=500 * 1024 * 1024,  # 500 MB soft limit
                            ),
                        ], width=10),
                    ], className="mb-2"),

                    # Dimension inputs (always required)
                    dbc.Row([
                        dbc.Col([dbc.Label("Nx (dim 0)"),
                                 dbc.Input(id=ids.GEOMETRY_NX, type="number", min=1, step=1,
                                           placeholder="e.g. 256")], width=3),
                        dbc.Col([dbc.Label("Ny (dim 1)"),
                                 dbc.Input(id=ids.GEOMETRY_NY, type="number", min=1, step=1,
                                           placeholder="e.g. 256")], width=3),
                        dbc.Col([dbc.Label("Nz (dim 2)"),
                                 dbc.Input(id=ids.GEOMETRY_NZ, type="number", min=1, step=1,
                                           placeholder="e.g. 256")], width=3),
                        dbc.Col([
                            dbc.Label("\u00a0"),  # spacer
                            dbc.Button("Load", id=ids.GEOMETRY_LOAD_BTN,
                                       color="primary", className="d-block"),
                        ], width=3),
                    ], className="mb-1"),
                    html.Small(
                        "Dimensions must be provided explicitly — the file is a flat binary array "
                        "with no header.",
                        className="text-muted",
                    ),

                    # Info banner after load
                    html.Div(id=ids.GEOMETRY_INFO, className="mt-2"),

                    html.Hr(),

                    # Body force panel
                    html.H5("Body Force (F vector)"),
                    dbc.Row([
                        dbc.Col([dbc.Label("Fx"), dbc.Input(id=ids.FLOW_F_X, type="number", value=0.0, step="any")], width=3),
                        dbc.Col([dbc.Label("Fy"), dbc.Input(id=ids.FLOW_F_Y, type="number", value=0.0, step="any")], width=3),
                        dbc.Col([dbc.Label("Fz"), dbc.Input(id=ids.FLOW_F_Z, type="number", value=1e-5, step="any")], width=3),
                    ], className="mb-3"),

                    html.Hr(),

                    # Slice viewer
                    html.H5("Geometry Slice Viewer"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Axis"),
                            dbc.Select(
                                id=ids.GEOMETRY_SLICE_AXIS,
                                options=[
                                    {"label": "X (dim 0)", "value": "0"},
                                    {"label": "Y (dim 1)", "value": "1"},
                                    {"label": "Z (dim 2)", "value": "2"},
                                ],
                                value="2",
                            ),
                        ], width=3),
                        dbc.Col([
                            dbc.Label("Slice index"),
                            dcc.Slider(id=ids.GEOMETRY_SLICE_INDEX, min=0, max=1,
                                       step=1, value=0, marks=None,
                                       tooltip={"placement": "bottom", "always_visible": True}),
                        ], width=9),
                    ], className="mb-4"),
                    dcc.Graph(id=ids.GEOMETRY_SLICE, style={"height": "400px"}),

                    # Hidden store for geometry array (small geometries) or path
                    dcc.Store(id="geometry-store"),
                ]),
            ],
        ),

        # ---- Section 2: Domain Configuration ----
        dbc.Card(
            className="mb-3",
            children=[
                dbc.CardHeader(html.H4("2. Domain Configuration", className="mb-0")),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("nproc [px, py, pz]"),
                            dbc.Input(id=ids.DOMAIN_NPROC, type="text",
                                      value="1, 1, 1",
                                      placeholder="1, 1, 1"),
                            html.Small("Process grid. Start with z-axis decomposition "
                                       "(e.g. 1, 1, 4).", className="text-muted"),
                        ], width=4),
                        dbc.Col([
                            dbc.Label("n (subdomain) [nx, ny, nz]"),
                            dbc.Input(id=ids.DOMAIN_N_SUBDOM, type="text",
                                      placeholder="auto-computed from N / nproc"),
                            html.Small("Must satisfy n[i] × nproc[i] ≤ N[i].",
                                       className="text-muted"),
                        ], width=4),
                        dbc.Col([
                            dbc.Label("Validation"),
                            html.Div(id=ids.VALIDATION_BADGE),
                        ], width=4),
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col([
                            dbc.Label("voxel_length"),
                            dbc.Input(id=ids.DOMAIN_VOXLEN, type="number",
                                      value=1.0, min=0, step=0.001),
                        ], width=3),
                        dbc.Col([
                            dbc.Label("Boundary condition (BC)"),
                            dbc.Select(
                                id=ids.DOMAIN_BC,
                                options=[
                                    {"label": "0 — Periodic", "value": "0"},
                                    {"label": "3 — Constant pressure", "value": "3"},
                                    {"label": "4 — Constant volumetric flux", "value": "4"},
                                ],
                                value="0",
                            ),
                        ], width=4),
                    ], className="mb-2"),

                    # Dynamic BC parameter fields
                    html.Div(id=ids.DOMAIN_BC_PARAMS, children=[
                        dbc.Row(id="bc-pressure-row", style={"display": "none"}, children=[
                            dbc.Col([
                                dbc.Label("din (inlet pressure)"),
                                dbc.Input(id=ids.DOMAIN_DIN, type="number", value=1.0, step=0.001),
                            ], width=3),
                            dbc.Col([
                                dbc.Label("dout (outlet pressure)"),
                                dbc.Input(id=ids.DOMAIN_DOUT, type="number", value=1.0, step=0.001),
                            ], width=3),
                        ], className="mb-3"),
                        dbc.Row(id="bc-flux-row", style={"display": "none"}, children=[
                            dbc.Col([
                                dbc.Label("flux (volumetric flux)"),
                                dbc.Input(id=ids.DOMAIN_FLUX, type="number", value=0.0, step=0.0001),
                            ], width=3),
                        ], className="mb-3"),
                    ]),

                    dbc.Row([
                        dbc.Col([
                            dbc.Label("ReadValues (from image)"),
                            html.Div(id=ids.DOMAIN_READ_VALUES_DISPLAY,
                                     children=html.Small("Load a geometry file first.",
                                                          className="text-muted")),
                            dbc.Input(id=ids.DOMAIN_READ_VALUES, type="hidden", value=""),
                        ], width=4),
                        dbc.Col([
                            dbc.Label("WriteValues (LBPM labels)"),
                            dbc.Input(id=ids.DOMAIN_WRITE_VALUES, type="text",
                                      placeholder="e.g. 0, 1, 2"),
                            dbc.Tooltip(
                                "Remap image labels to LBPM convention: values ≤ 0 = solid, "
                                "1 = NWP (non-wetting phase), 2 = WP (wetting phase). "
                                "Edit WriteValues to match this convention before running.",
                                target=ids.DOMAIN_WRITE_VALUES,
                                placement="right",
                            ),
                        ], width=4),
                        dbc.Col([
                            dbc.Label("ComponentLabels (solid)"),
                            dbc.Input(id=ids.DOMAIN_COMPONENT_LABELS, type="text",
                                      placeholder="auto from WriteValues ≤ 0"),
                            html.Small("Auto-derived; edit if needed.", className="text-muted"),
                        ], width=4),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Filename (geometry file)"),
                            dbc.Input(id=ids.DOMAIN_FILENAME, type="text",
                                      placeholder="e.g. geometry.raw"),
                            html.Small("Auto-populated from path; edit if needed.", className="text-muted"),
                        ], width=6),
                        dbc.Col([
                            dbc.Label("offset"),
                            dbc.Input(id=ids.DOMAIN_OFFSET, type="number",
                                      value=0, min=0, step=1),
                            html.Small("Starting voxel offset into the file (default 0).", className="text-muted"),
                        ], width=3),
                    ], className="mt-3"),
                ]),
            ],
        ),

        # ---- Section 3: Simulation Model Configuration ----
        dbc.Card(
            className="mb-3",
            children=[
                dbc.CardHeader(html.H4("3. Simulation Model Configuration", className="mb-0")),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Simulation model"),
                            dbc.Select(
                                id=ids.MODEL_SELECTOR,
                                options=[
                                    {"label": "Color (two-phase flow)", "value": "color"},
                                    {"label": "Permeability (single-phase MRT)", "value": "perm"},
                                    {"label": "Morphology (pre-analysis)", "value": "morph"},
                                ],
                                value="color",
                            ),
                        ], width=4),
                    ], className="mb-3"),

                    # Color model params
                    html.Div(id="color-params", children=[
                        html.H5("Color Model Parameters"),
                        dbc.Row([
                            dbc.Col([dbc.Label("tauA"), dbc.Input(id=ids.COLOR_TAU_A, type="number", value=0.7, step=0.01)], width=2),
                            dbc.Col([dbc.Label("tauB"), dbc.Input(id=ids.COLOR_TAU_B, type="number", value=0.7, step=0.01)], width=2),
                            dbc.Col([dbc.Label("rhoA"), dbc.Input(id=ids.COLOR_RHO_A, type="number", value=1.0, step=0.01)], width=2),
                            dbc.Col([dbc.Label("rhoB"), dbc.Input(id=ids.COLOR_RHO_B, type="number", value=1.0, step=0.01)], width=2),
                            dbc.Col([dbc.Label("alpha (interfacial tension)"), dbc.Input(id=ids.COLOR_ALPHA, type="number", value=0.01, step=0.001)], width=2),
                            dbc.Col([dbc.Label("beta (sharpness)"), dbc.Input(id=ids.COLOR_BETA, type="number", value=0.95, step=0.01)], width=2),
                        ], className="mb-2"),
                        dbc.Row([
                            dbc.Col([dbc.Label("capillary_number"), dbc.Input(id=ids.COLOR_CAP_NUM, type="number", value=1e-5, step=1e-6)], width=3),
                            dbc.Col([dbc.Label("timestepMax"), dbc.Input(id=ids.COLOR_TIMESTEP_MAX, type="number", value=10000000, step=1000)], width=3),
                            dbc.Col([dbc.Label("Protocol"),
                                     dbc.Select(id=ids.COLOR_PROTOCOL,
                                                options=[
                                                    {"label": "fractional flow", "value": "fractional flow"},
                                                    {"label": "centrifuge", "value": "centrifuge"},
                                                    {"label": "core flooding", "value": "core flooding"},
                                                    {"label": "image sequence", "value": "image sequence"},
                                                    {"label": "user specified", "value": "user specified"},
                                                ],
                                                value="fractional flow")], width=3),
                            dbc.Col([dbc.Label("Restart"), dbc.Checklist(id=ids.COLOR_RESTART,
                                     options=[{"label": "Enable restart", "value": "true"}],
                                     value=[])], width=3),
                        ], className="mb-2"),
                        dbc.Row([
                            dbc.Col([dbc.Label("inletLayers [x,y,z]"), dbc.Input(id=ids.COLOR_INLET_LAYERS, type="text", value="0, 0, 5")], width=3),
                            dbc.Col([dbc.Label("outletLayers [x,y,z]"), dbc.Input(id=ids.COLOR_OUTLET_LAYERS, type="text", value="0, 0, 5")], width=3),
                            dbc.Col([dbc.Label("ComponentAffinity (wetting per solid label)"),
                                     dbc.Input(id=ids.COLOR_COMPONENT_AFFINITY, type="text",
                                               placeholder="e.g. 1.0  (one value per ComponentLabel)")], width=6),
                        ], className="mb-2"),

                        # FlowAdaptor
                        html.H6("FlowAdaptor (fractional flow control)", className="mt-3"),
                        dbc.Row([
                            dbc.Col([dbc.Label("max_steady_timesteps"), dbc.Input(id=ids.FA_MAX_STEADY, type="number", value=200000, step=1000)], width=3),
                            dbc.Col([dbc.Label("min_steady_timesteps"), dbc.Input(id=ids.FA_MIN_STEADY, type="number", value=100000, step=1000)], width=3),
                            dbc.Col([dbc.Label("fractional_flow_increment"), dbc.Input(id=ids.FA_FF_INCREMENT, type="number", value=0.1, step=0.01)], width=3),
                            dbc.Col([dbc.Label("mass_fraction_factor"), dbc.Input(id=ids.FA_MASS_FRACTION, type="number", value=0.0002, step=0.00001)], width=3),
                        ], className="mb-2"),
                        dbc.Row([
                            dbc.Col([dbc.Label("endpoint_threshold"), dbc.Input(id=ids.FA_ENDPOINT_THRESH, type="number", value=0.1, step=0.01)], width=3),
                        ]),
                    ]),

                    # Permeability model params (hidden by default)
                    html.Div(id="perm-params", style={"display": "none"}, children=[
                        html.H5("Permeability Model Parameters"),
                        dbc.Row([
                            dbc.Col([dbc.Label("tau"), dbc.Input(id="perm-tau", type="number", value=0.7, step=0.01)], width=3),
                            dbc.Col([dbc.Label("tolerance"), dbc.Input(id="perm-tolerance", type="number", value=1e-6, step=1e-7)], width=3),
                            dbc.Col([dbc.Label("timestepMax"), dbc.Input(id="perm-timestep-max", type="number", value=10000000, step=1000)], width=3),
                        ]),
                    ]),

                    # Morphology model params (hidden by default)
                    html.Div(id="morph-params", style={"display": "none"}, children=[
                        html.H5("Morphology Parameters"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Operation"),
                                dbc.RadioItems(
                                    id="morph-operation",
                                    options=[
                                        {"label": "Drainage", "value": "drainage"},
                                        {"label": "Opening", "value": "opening"},
                                    ],
                                    value="drainage",
                                    inline=True,
                                ),
                                html.Small(
                                    "Target saturation for morphological drainage is set in the "
                                    "Domain section.",
                                    className="text-muted",
                                ),
                            ], width=6),
                        ]),
                    ]),

                    html.Hr(),

                    # Analysis section (all models)
                    html.H5("Analysis Settings"),
                    dbc.Row([
                        dbc.Col([dbc.Label("analysis_interval"), dbc.Input(id=ids.ANALYSIS_INTERVAL, type="number", value=1000, step=100)], width=3),
                        dbc.Col([dbc.Label("subphase_analysis_interval"), dbc.Input(id=ids.ANALYSIS_SUBPHASE_INTERVAL, type="number", value=5000, step=100)], width=3),
                        dbc.Col([dbc.Label("visualization_interval"), dbc.Input(id=ids.ANALYSIS_VIS_INTERVAL, type="number", value=10000, step=1000)], width=3),
                    ], className="mb-2"),
                    dbc.Row([
                        dbc.Col([dbc.Label("N_threads"), dbc.Input(id=ids.ANALYSIS_N_THREADS, type="number", value=4, min=1, step=1)], width=3),
                        dbc.Col([dbc.Label("restart_interval"), dbc.Input(id=ids.ANALYSIS_RESTART_INTERVAL, type="number", value=1000000, step=100000)], width=3),
                    ], className="mb-3"),

                    html.H5("Visualization Settings"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Checklist(
                                id=ids.VIS_SAVE_8BIT,
                                options=[{"label": "save_8bit_raw", "value": "true"}],
                                value=["true"],
                            ),
                        ], width=3),
                        dbc.Col([
                            dbc.Checklist(
                                id=ids.VIS_SAVE_PHASE,
                                options=[{"label": "save_phase_field", "value": "true"}],
                                value=["true"],
                            ),
                        ], width=3),
                        dbc.Col([
                            dbc.Checklist(
                                id=ids.VIS_SAVE_PRESSURE,
                                options=[{"label": "save_pressure_field", "value": "true"}],
                                value=["true"],
                            ),
                        ], width=3),
                        dbc.Col([
                            dbc.Checklist(
                                id=ids.VIS_SAVE_VELOCITY,
                                options=[{"label": "save_velocity_field", "value": "true"}],
                                value=["true"],
                            ),
                        ], width=3),
                    ]),
                ]),
            ],
        ),

        # ---- Section 4: Create Simulation Directory ----
        dbc.Card(
            className="mb-3",
            children=[
                dbc.CardHeader(html.H4("4. Create Simulation Directory", className="mb-0")),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Remote base path"),
                            dbc.Input(id=ids.REMOTE_BASE_PATH, type="text",
                                      placeholder="/scratch/user/simulations"),
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Simulation directory name"),
                            dbc.Input(id=ids.SIM_NAME_INPUT, type="text",
                                      placeholder="e.g. berea_color_run1"),
                        ], width=4),
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Preview input.db", id=ids.PREVIEW_INPUT_DB_BTN,
                                       color="secondary", className="me-2"),
                            dbc.Button("Create & Upload", id=ids.CREATE_SIM_BTN,
                                       color="success"),
                        ]),
                    ], className="mb-3"),

                    # Progress bar for file upload
                    dbc.Progress(id=ids.UPLOAD_PROGRESS, value=0, max=100,
                                 style={"display": "none"}, className="mb-2"),
                    dcc.Interval(id=ids.UPLOAD_PROGRESS_INTERVAL, interval=1000,
                                 disabled=True),
                    dcc.Store(id="upload-progress-store", data={"pct": 0, "active": False}),

                    # Status messages
                    html.Div(id=ids.CREATE_STATUS),

                    # Preview modal
                    dbc.Modal(
                        id=ids.INPUT_DB_PREVIEW_MODAL,
                        size="lg",
                        children=[
                            dbc.ModalHeader("input.db Preview"),
                            dbc.ModalBody(
                                dcc.Markdown(id=ids.INPUT_DB_PREVIEW_CONTENT,
                                             style={"whiteSpace": "pre", "fontFamily": "monospace"})
                            ),
                            dbc.ModalFooter(
                                dbc.Button("Close", id="preview-modal-close", className="ms-auto")
                            ),
                        ],
                    ),
                ]),
            ],
        ),
    ],
)


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@callback(
    Output("geometry-path-row", "style"),
    Output("geometry-upload-row", "style"),
    Input(ids.GEOMETRY_SOURCE_RADIO, "value"),
)
def toggle_source(source):
    if source == "path":
        return {}, {"display": "none"}
    return {"display": "none"}, {}



@callback(
    Output(ids.GEOMETRY_INFO, "children"),
    Output(ids.GEOMETRY_SLICE_INDEX, "max"),
    Output(ids.GEOMETRY_SLICE_INDEX, "value"),
    Output("geometry-store", "data"),
    Output(ids.DOMAIN_READ_VALUES_DISPLAY, "children"),
    Output(ids.DOMAIN_READ_VALUES, "value"),
    Output(ids.DOMAIN_WRITE_VALUES, "value"),
    Output(ids.DOMAIN_COMPONENT_LABELS, "value"),
    Output(ids.DOMAIN_N_SUBDOM, "value"),
    Input(ids.GEOMETRY_LOAD_BTN, "n_clicks"),
    State(ids.GEOMETRY_SOURCE_RADIO, "value"),
    State(ids.GEOMETRY_REMOTE_PATH, "value"),
    State(ids.GEOMETRY_UPLOAD, "contents"),
    State(ids.GEOMETRY_NX, "value"),
    State(ids.GEOMETRY_NY, "value"),
    State(ids.GEOMETRY_NZ, "value"),
    State(ids.DOMAIN_NPROC, "value"),
    prevent_initial_call=True,
)
def load_geometry(n_clicks, source, remote_path, upload_contents, nx, ny, nz, nproc_str):
    if not nx or not ny or not nz:
        return (
            dbc.Alert("Please enter Nx, Ny, Nz before loading.", color="danger"),
            1, 0, None,
            html.Small("Load a geometry file first.", className="text-muted"),
            "", "", "", "",
        )

    nx, ny, nz = int(nx), int(ny), int(nz)
    expected_bytes = nx * ny * nz

    try:
        if source == "path":
            if not remote_path:
                raise ValueError("Please enter a file path.")
            from pyLBPM.filesystem import get_filesystem
            fs = get_filesystem()
            raw_bytes = fs.read_file(remote_path)
        else:
            if not upload_contents:
                raise ValueError("Please upload a file.")
            content_type, content_string = upload_contents.split(",", 1)
            raw_bytes = base64.b64decode(content_string)

        actual_bytes = len(raw_bytes)
        if actual_bytes != expected_bytes:
            raise ValueError(
                f"File size ({actual_bytes:,} bytes) does not match "
                f"Nx×Ny×Nz = {nx}×{ny}×{nz} = {expected_bytes:,} bytes (uint8). "
                f"Check dimensions."
            )

        arr = np.frombuffer(raw_bytes, dtype=np.uint8).reshape(nx, ny, nz)
        labels = np.unique(arr).tolist()

        info = dbc.Alert(
            [
                html.B("Loaded successfully. "),
                f"Size: {actual_bytes:,} bytes | "
                f"Shape: {nx}×{ny}×{nz} | "
                f"Labels: {labels}",
            ],
            color="success",
        )

        labels_str = ", ".join(str(v) for v in labels)
        write_values_default = labels_str
        solid_labels = [str(v) for v in labels if v <= 0]
        component_labels_default = ", ".join(solid_labels) if solid_labels else ""

        # Compute default subdomain size (start with z-axis)
        try:
            nproc = [int(x.strip()) for x in nproc_str.split(",")]
        except Exception:
            nproc = [1, 1, 1]
        n_sub = [nx // nproc[0], ny // nproc[1], nz // nproc[2]]
        n_sub_str = ", ".join(str(v) for v in n_sub)

        # Store only the raw bytes encoded as base64 to avoid memory issues
        store_data = {
            "nx": nx, "ny": ny, "nz": nz,
            "b64": base64.b64encode(raw_bytes).decode(),
        }

        return (
            info,
            nz - 1, nz // 2,
            store_data,
            html.Code(labels_str),
            labels_str,
            write_values_default,
            component_labels_default,
            n_sub_str,
        )

    except Exception as e:
        return (
            dbc.Alert(f"Error loading geometry: {e}", color="danger"),
            1, 0, None,
            html.Small("Load a geometry file first.", className="text-muted"),
            "", "", "", "",
        )


@callback(
    Output(ids.GEOMETRY_SLICE, "figure"),
    Input(ids.GEOMETRY_SLICE_AXIS, "value"),
    Input(ids.GEOMETRY_SLICE_INDEX, "value"),
    State("geometry-store", "data"),
    prevent_initial_call=True,
)
def update_slice(axis_str, slice_idx, store_data):
    if not store_data:
        return {}
    axis = int(axis_str)
    nx, ny, nz = store_data["nx"], store_data["ny"], store_data["nz"]
    raw_bytes = base64.b64decode(store_data["b64"])
    arr = np.frombuffer(raw_bytes, dtype=np.uint8).reshape(nx, ny, nz)

    axis_labels = ["X (dim 0)", "Y (dim 1)", "Z (dim 2)"]
    if axis == 0:
        s = arr[slice_idx, :, :]
        xlabel, ylabel = "Y", "Z"
    elif axis == 1:
        s = arr[:, slice_idx, :]
        xlabel, ylabel = "X", "Z"
    else:
        s = arr[:, :, slice_idx]
        xlabel, ylabel = "X", "Y"

    fig = px.imshow(
        s,
        color_continuous_scale="gray",
        labels={"x": xlabel, "y": ylabel, "color": "label"},
        title=f"Slice along {axis_labels[axis]} = {slice_idx}",
        aspect="equal",
    )
    fig.update_layout(margin=dict(l=40, r=10, t=40, b=30))
    return fig


@callback(
    Output(ids.VALIDATION_BADGE, "children"),
    Input(ids.DOMAIN_NPROC, "value"),
    Input(ids.DOMAIN_N_SUBDOM, "value"),
    State(ids.GEOMETRY_NX, "value"),
    State(ids.GEOMETRY_NY, "value"),
    State(ids.GEOMETRY_NZ, "value"),
)
def validate_decomp(nproc_str, n_sub_str, nx, ny, nz):
    if not nx or not ny or not nz or not nproc_str or not n_sub_str:
        return dbc.Badge("—", color="secondary")
    try:
        N = [int(nx), int(ny), int(nz)]
        nproc = [int(x.strip()) for x in nproc_str.split(",")]
        n_sub = [int(x.strip()) for x in n_sub_str.split(",")]
        ok = all(n_sub[i] * nproc[i] <= N[i] for i in range(3))
        if ok:
            return dbc.Badge("Valid ✓", color="success")
        violations = [
            f"dim {i}: {n_sub[i]}×{nproc[i]}={n_sub[i]*nproc[i]} > N[{i}]={N[i]}"
            for i in range(3) if n_sub[i] * nproc[i] > N[i]
        ]
        return dbc.Badge(f"Invalid: {'; '.join(violations)}", color="danger")
    except Exception:
        return dbc.Badge("Check values", color="warning")


@callback(
    Output(ids.DOMAIN_COMPONENT_LABELS, "value", allow_duplicate=True),
    Input(ids.DOMAIN_WRITE_VALUES, "value"),
    prevent_initial_call=True,
)
def auto_component_labels(write_values_str):
    if not write_values_str:
        return ""
    try:
        vals = [int(x.strip()) for x in write_values_str.split(",")]
        solid = [str(v) for v in vals if v <= 0]
        return ", ".join(solid)
    except Exception:
        return ""


@callback(
    Output(ids.DOMAIN_FILENAME, "value"),
    Input(ids.GEOMETRY_REMOTE_PATH, "value"),
    prevent_initial_call=True,
)
def auto_filename(remote_path):
    if not remote_path:
        return ""
    from pathlib import Path
    return Path(remote_path).name


@callback(
    Output("bc-pressure-row", "style"),
    Output("bc-flux-row", "style"),
    Input(ids.DOMAIN_BC, "value"),
)
def toggle_bc_params(bc):
    show = {}
    hide = {"display": "none"}
    return (
        show if bc == "3" else hide,
        show if bc == "4" else hide,
    )


@callback(
    Output("color-params", "style"),
    Output("perm-params", "style"),
    Output("morph-params", "style"),
    Input(ids.MODEL_SELECTOR, "value"),
)
def toggle_model_params(model):
    show = {}
    hide = {"display": "none"}
    return (
        show if model == "color" else hide,
        show if model == "perm" else hide,
        show if model == "morph" else hide,
    )


def _build_input_db(
    nx, ny, nz, nproc_str, n_sub_str, voxlen, bc,
    din, dout, flux,
    read_values_str, write_values_str, component_labels_str,
    filename, offset,
    model, f_x, f_y, f_z,
    tau_a, tau_b, rho_a, rho_b, alpha, beta, cap_num, timestep_max,
    restart, protocol, inlet_layers_str, outlet_layers_str, affinity_str,
    fa_max, fa_min, fa_incr, fa_mass, fa_ep,
    perm_tau, perm_tolerance, perm_timestep_max,
    analysis_interval, subphase_interval, vis_interval, n_threads, restart_interval,
    save_8bit, save_phase, save_pressure, save_velocity,
):
    """Generate the full input.db text string from form values."""
    def parse_list(s):
        return [x.strip() for x in (s or "").split(",") if x.strip()]

    nproc = parse_list(nproc_str) or ["1", "1", "1"]
    n_sub = parse_list(n_sub_str) or [str(int(nx) // int(p)) for p, nx_ in zip(nproc, [nx, ny, nz])]
    read_vals = parse_list(read_values_str)
    write_vals = parse_list(write_values_str) or read_vals
    comp_labels = parse_list(component_labels_str)

    # Determine F vector
    fx = float(f_x) if f_x is not None else 0.0
    fy = float(f_y) if f_y is not None else 0.0
    fz = float(f_z) if f_z is not None else 1e-5
    f_str = f"{fx}, {fy}, {fz}"

    db = "Domain {\n"
    db += f'   ReadType = "8bit"\n'
    if filename:
        db += f'   Filename = "{filename}"\n'
    db += f"   offset = {int(offset) if offset is not None else 0}\n"
    db += f"   voxel_length = {voxlen}\n"
    db += f"   N = {nx}, {ny}, {nz}\n"
    db += f"   nproc = {', '.join(nproc)}\n"
    db += f"   n = {', '.join(str(v) for v in n_sub)}\n"
    db += f"   ReadValues = {', '.join(read_vals)}\n"
    db += f"   WriteValues = {', '.join(write_vals)}\n"
    db += f"   ComponentLabels = {', '.join(comp_labels)}\n"
    db += f"   BC = {bc}\n"
    if str(bc) == "3":
        db += f"   din = {din if din is not None else 1.0}\n"
        db += f"   dout = {dout if dout is not None else 1.0}\n"
    elif str(bc) == "4":
        db += f"   flux = {flux if flux is not None else 0.0}\n"
    db += "}\n\n"

    if model == "color":
        restart_val = "true" if "true" in (restart or []) else "false"
        db += "Color {\n"
        if protocol and protocol != "user specified":
            db += f'   protocol = "{protocol}"\n'
        db += f"   Restart = {restart_val}\n"
        db += '   WettingConvention = "SCAL"\n'
        db += f"   ComponentLabels = {', '.join(comp_labels)}\n"
        affinity = parse_list(affinity_str) or ["1.0"] * len(comp_labels)
        db += f"   ComponentAffinity = {', '.join(affinity)}\n"
        db += f"   timestepMax = {timestep_max}\n"
        db += f"   tauA = {tau_a}\n"
        db += f"   tauB = {tau_b}\n"
        db += f"   rhoA = {rho_a}\n"
        db += f"   rhoB = {rho_b}\n"
        db += f"   alpha = {alpha}\n"
        db += f"   beta = {beta}\n"
        db += f"   capillary_number = {cap_num}\n"
        db += f"   F = {f_str}\n"
        db += f"   inletLayers = {inlet_layers_str}\n"
        db += f"   outletLayers = {outlet_layers_str}\n"
        db += "}\n\n"

        db += "FlowAdaptor {\n"
        db += f"   max_steady_timesteps = {fa_max}\n"
        db += f"   min_steady_timesteps = {fa_min}\n"
        db += f"   fractional_flow_increment = {fa_incr}\n"
        db += f"   mass_fraction_factor = {fa_mass}\n"
        db += f"   endpoint_threshold = {fa_ep}\n"
        db += "}\n\n"

    elif model == "perm":
        db += "MRT {\n"
        db += f"   F = {f_str}\n"
        db += f"   tau = {perm_tau if perm_tau is not None else 0.7}\n"
        db += f"   tolerance = {perm_tolerance if perm_tolerance is not None else 1e-6}\n"
        db += f"   timestepMax = {perm_timestep_max if perm_timestep_max is not None else 10000000}\n"
        db += "}\n\n"

    db += "Analysis {\n"
    db += '   restart_file = "Restart"\n'
    db += f"   analysis_interval = {analysis_interval}\n"
    db += f"   subphase_analysis_interval = {subphase_interval}\n"
    db += f"   visualization_interval = {vis_interval}\n"
    db += f"   N_threads = {n_threads}\n"
    db += f"   restart_interval = {restart_interval}\n"
    db += "}\n\n"

    db += "Visualization {\n"
    db += '   format = "hdf5"\n'
    db += "   write_silo = true\n"
    db += f"   save_8bit_raw = {'true' if 'true' in (save_8bit or []) else 'false'}\n"
    db += f"   save_phase_field = {'true' if 'true' in (save_phase or []) else 'false'}\n"
    db += f"   save_pressure_field = {'true' if 'true' in (save_pressure or []) else 'false'}\n"
    db += f"   save_velocity_field = {'true' if 'true' in (save_velocity or []) else 'false'}\n"
    db += "}\n"

    return db


@callback(
    Output(ids.INPUT_DB_PREVIEW_MODAL, "is_open"),
    Output(ids.INPUT_DB_PREVIEW_CONTENT, "children"),
    Input(ids.PREVIEW_INPUT_DB_BTN, "n_clicks"),
    Input("preview-modal-close", "n_clicks"),
    State(ids.GEOMETRY_NX, "value"),
    State(ids.GEOMETRY_NY, "value"),
    State(ids.GEOMETRY_NZ, "value"),
    State(ids.DOMAIN_NPROC, "value"),
    State(ids.DOMAIN_N_SUBDOM, "value"),
    State(ids.DOMAIN_VOXLEN, "value"),
    State(ids.DOMAIN_BC, "value"),
    State(ids.DOMAIN_DIN, "value"),
    State(ids.DOMAIN_DOUT, "value"),
    State(ids.DOMAIN_FLUX, "value"),
    State(ids.DOMAIN_READ_VALUES, "value"),
    State(ids.DOMAIN_WRITE_VALUES, "value"),
    State(ids.DOMAIN_COMPONENT_LABELS, "value"),
    State(ids.DOMAIN_FILENAME, "value"),
    State(ids.DOMAIN_OFFSET, "value"),
    State(ids.MODEL_SELECTOR, "value"),
    State(ids.FLOW_F_X, "value"),
    State(ids.FLOW_F_Y, "value"),
    State(ids.FLOW_F_Z, "value"),
    State(ids.COLOR_TAU_A, "value"),
    State(ids.COLOR_TAU_B, "value"),
    State(ids.COLOR_RHO_A, "value"),
    State(ids.COLOR_RHO_B, "value"),
    State(ids.COLOR_ALPHA, "value"),
    State(ids.COLOR_BETA, "value"),
    State(ids.COLOR_CAP_NUM, "value"),
    State(ids.COLOR_TIMESTEP_MAX, "value"),
    State(ids.COLOR_RESTART, "value"),
    State(ids.COLOR_PROTOCOL, "value"),
    State(ids.COLOR_INLET_LAYERS, "value"),
    State(ids.COLOR_OUTLET_LAYERS, "value"),
    State(ids.COLOR_COMPONENT_AFFINITY, "value"),
    State(ids.FA_MAX_STEADY, "value"),
    State(ids.FA_MIN_STEADY, "value"),
    State(ids.FA_FF_INCREMENT, "value"),
    State(ids.FA_MASS_FRACTION, "value"),
    State(ids.FA_ENDPOINT_THRESH, "value"),
    State("perm-tau", "value"),
    State("perm-tolerance", "value"),
    State("perm-timestep-max", "value"),
    State(ids.ANALYSIS_INTERVAL, "value"),
    State(ids.ANALYSIS_SUBPHASE_INTERVAL, "value"),
    State(ids.ANALYSIS_VIS_INTERVAL, "value"),
    State(ids.ANALYSIS_N_THREADS, "value"),
    State(ids.ANALYSIS_RESTART_INTERVAL, "value"),
    State(ids.VIS_SAVE_8BIT, "value"),
    State(ids.VIS_SAVE_PHASE, "value"),
    State(ids.VIS_SAVE_PRESSURE, "value"),
    State(ids.VIS_SAVE_VELOCITY, "value"),
    prevent_initial_call=True,
)
def toggle_preview(preview_clicks, close_clicks, *args):
    triggered = dash.callback_context.triggered[0]["prop_id"]
    if "preview-modal-close" in triggered:
        return False, ""
    try:
        db_text = _build_input_db(*args)
        return True, f"```\n{db_text}\n```"
    except Exception as e:
        return True, f"Error generating input.db: {e}"


@callback(
    Output(ids.CREATE_STATUS, "children"),
    Input(ids.CREATE_SIM_BTN, "n_clicks"),
    State(ids.REMOTE_BASE_PATH, "value"),
    State(ids.SIM_NAME_INPUT, "value"),
    State(ids.GEOMETRY_SOURCE_RADIO, "value"),
    State(ids.GEOMETRY_REMOTE_PATH, "value"),
    State("geometry-store", "data"),
    State(ids.GEOMETRY_NX, "value"),
    State(ids.GEOMETRY_NY, "value"),
    State(ids.GEOMETRY_NZ, "value"),
    State(ids.DOMAIN_NPROC, "value"),
    State(ids.DOMAIN_N_SUBDOM, "value"),
    State(ids.DOMAIN_VOXLEN, "value"),
    State(ids.DOMAIN_BC, "value"),
    State(ids.DOMAIN_DIN, "value"),
    State(ids.DOMAIN_DOUT, "value"),
    State(ids.DOMAIN_FLUX, "value"),
    State(ids.DOMAIN_READ_VALUES, "value"),
    State(ids.DOMAIN_WRITE_VALUES, "value"),
    State(ids.DOMAIN_COMPONENT_LABELS, "value"),
    State(ids.DOMAIN_FILENAME, "value"),
    State(ids.DOMAIN_OFFSET, "value"),
    State(ids.MODEL_SELECTOR, "value"),
    State(ids.FLOW_F_X, "value"),
    State(ids.FLOW_F_Y, "value"),
    State(ids.FLOW_F_Z, "value"),
    State(ids.COLOR_TAU_A, "value"),
    State(ids.COLOR_TAU_B, "value"),
    State(ids.COLOR_RHO_A, "value"),
    State(ids.COLOR_RHO_B, "value"),
    State(ids.COLOR_ALPHA, "value"),
    State(ids.COLOR_BETA, "value"),
    State(ids.COLOR_CAP_NUM, "value"),
    State(ids.COLOR_TIMESTEP_MAX, "value"),
    State(ids.COLOR_RESTART, "value"),
    State(ids.COLOR_PROTOCOL, "value"),
    State(ids.COLOR_INLET_LAYERS, "value"),
    State(ids.COLOR_OUTLET_LAYERS, "value"),
    State(ids.COLOR_COMPONENT_AFFINITY, "value"),
    State(ids.FA_MAX_STEADY, "value"),
    State(ids.FA_MIN_STEADY, "value"),
    State(ids.FA_FF_INCREMENT, "value"),
    State(ids.FA_MASS_FRACTION, "value"),
    State(ids.FA_ENDPOINT_THRESH, "value"),
    State("perm-tau", "value"),
    State("perm-tolerance", "value"),
    State("perm-timestep-max", "value"),
    State(ids.ANALYSIS_INTERVAL, "value"),
    State(ids.ANALYSIS_SUBPHASE_INTERVAL, "value"),
    State(ids.ANALYSIS_VIS_INTERVAL, "value"),
    State(ids.ANALYSIS_N_THREADS, "value"),
    State(ids.ANALYSIS_RESTART_INTERVAL, "value"),
    State(ids.VIS_SAVE_8BIT, "value"),
    State(ids.VIS_SAVE_PHASE, "value"),
    State(ids.VIS_SAVE_PRESSURE, "value"),
    State(ids.VIS_SAVE_VELOCITY, "value"),
    prevent_initial_call=True,
)
def create_simulation_directory(
    n_clicks, base_path, sim_name,
    geo_source, geo_remote_path, geo_store,
    *db_args,
):
    if not base_path or not sim_name:
        return dbc.Alert("Please enter a base path and simulation name.", color="danger")

    import posixpath
    sim_dir = posixpath.join(base_path.rstrip("/"), sim_name)

    steps = []
    try:
        from pyLBPM.filesystem import get_filesystem
        fs = get_filesystem()

        # Step 1: create directory
        fs.mkdir(sim_dir)
        steps.append(dbc.ListGroupItem(f"✓ Created directory: {sim_dir}", color="success"))

        # Step 2: write input.db
        db_text = _build_input_db(*db_args)
        fs.write_file(posixpath.join(sim_dir, "input.db"), db_text.encode())
        steps.append(dbc.ListGroupItem("✓ Written: input.db", color="success"))

        # Step 3: place geometry file
        nx = db_args[0]
        if geo_source == "path" and geo_remote_path:
            from pathlib import Path as _Path
            geo_filename = _Path(geo_remote_path).name
            dst = posixpath.join(sim_dir, geo_filename)
            # For local backend: copy file
            fs.put_file(geo_remote_path, dst)
            steps.append(dbc.ListGroupItem(f"✓ Copied geometry: {geo_filename}", color="success"))
        elif geo_store:
            import base64 as _b64
            import tempfile, os
            raw_bytes = _b64.b64decode(geo_store["b64"])
            with tempfile.NamedTemporaryFile(delete=False, suffix=".raw") as tmp:
                tmp.write(raw_bytes)
                tmp_path = tmp.name
            geo_filename = sim_name + ".raw"
            dst = posixpath.join(sim_dir, geo_filename)
            fs.put_file(tmp_path, dst)
            os.unlink(tmp_path)
            steps.append(dbc.ListGroupItem(f"✓ Uploaded geometry: {geo_filename}", color="success"))
        else:
            steps.append(dbc.ListGroupItem(
                "⚠ No geometry file transferred — load a geometry file first.",
                color="warning",
            ))

    except Exception as e:
        steps.append(dbc.ListGroupItem(f"✗ Error: {e}", color="danger"))

    return dbc.ListGroup(steps)
