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
# Tooltip helper
# ---------------------------------------------------------------------------

def _tip(label_text, tip_id, tip_text="TODO"):
    """Return a label + hoverable ⓘ icon with a tooltip."""
    return html.Div([
        dbc.Label(label_text, className="me-1 mb-0"),
        html.Span("ⓘ", id=tip_id,
                  style={"cursor": "pointer", "color": "#6c757d",
                         "fontSize": "0.85em", "verticalAlign": "middle"}),
        dbc.Tooltip(tip_text, target=tip_id, style={"white-space": "pre-wrap"}),
    ], className="d-flex align-items-center mb-1")


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
                dbc.CardHeader(
                    dbc.Row([
                        dbc.Col(html.H4("1. Load Geometry File", className="mb-0")),
                        dbc.Col(
                            dbc.Button("Load New Geometry", id=ids.LOAD_NEW_GEOMETRY_BTN,
                                       color="outline-secondary", size="sm"),
                            width="auto",
                        ),
                    ], align="center"),
                ),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Source"),
                            dbc.RadioItems(
                                id=ids.GEOMETRY_SOURCE_RADIO,
                                options=[
                                    {"label": "Local path", "value": "path"},
                                    {"label": "Browser upload", "value": "upload"},
                                    {"label": "Create an input file without uploading a geometry", "value": "dims"},
                                ],
                                value="path",
                                inline=True,
                            ),
                        ], width=12),
                    ], className="mb-2"),

                    # Remote path input (shown when source=path)
                    dbc.Row(id="geometry-path-row", children=[
                        dbc.Col([
                            _tip("File path", ids.TOOLTIP_REMOTE_PATH, tip_text="Absolute path to the .raw geometry file."),
                            dbc.Input(
                                id=ids.GEOMETRY_REMOTE_PATH,
                                type="text",
                                placeholder="/scratch/user/sim/geometry.raw",
                            ),
                        ], width=10),
                    ], className="mb-2"),

                    # Dims-only info row (shown when source=dims)
                    dbc.Row(id="geometry-dims-row", style={"display": "none"}, children=[
                        dbc.Col([
                            dbc.Alert(
                                "No geometry file will be loaded or transferred. "
                                "You can edit all fields manually below.",
                                color="info",
                                className="mb-0",
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
                        dbc.Col([
                            _tip("Nx", ids.TOOLTIP_NX, tip_text="Number of voxels in the X dimension."),
                            dbc.Input(id=ids.GEOMETRY_NX, type="number", min=1, step=1,
                                      placeholder="e.g. 256"),
                        ], width=3),
                        dbc.Col([
                            _tip("Ny", ids.TOOLTIP_NY, tip_text="Number of voxels in the Y dimension."),
                            dbc.Input(id=ids.GEOMETRY_NY, type="number", min=1, step=1,
                                      placeholder="e.g. 256"),
                        ], width=3),
                        dbc.Col([
                            _tip("Nz", ids.TOOLTIP_NZ, tip_text="Number of voxels in the Z dimension."),
                            dbc.Input(id=ids.GEOMETRY_NZ, type="number", min=1, step=1,
                                      placeholder="e.g. 256"),
                        ], width=3),
                        dbc.Col([
                            dbc.Label("\u00a0"),  # spacer
                            dbc.Button("Load", id=ids.GEOMETRY_LOAD_BTN,
                                       color="primary", className="d-block"),
                        ], width=3),
                    ], className="mb-1"),
                    # html.Small(
                    #     "Dimensions must be provided explicitly — the file is a flat binary array "
                    #     "with no header.",
                    #     className="text-muted",
                    # ),

                    # Info banner after load
                    html.Div(id=ids.GEOMETRY_INFO, className="mt-2"),

                    html.Div(id=ids.GEOMETRY_SLICE_VIEWER, style={"display": "none"}, children=[
                        html.Hr(),

                        # Slice viewer
                        html.H5("Geometry Slice Viewer"),
                        dbc.Row([
                            dbc.Col([
                                _tip("Axis", ids.TOOLTIP_SLICE_AXIS, tip_text="Axis along which to view a slice."),
                                dbc.Select(
                                    id=ids.GEOMETRY_SLICE_AXIS,
                                    options=[
                                        {"label": "Z (dim 0)", "value": "0"},
                                        {"label": "Y (dim 1)", "value": "1"},
                                        {"label": "X (dim 2)", "value": "2"},
                                    ],
                                    value="0",
                                ),
                            ], width=3),
                            dbc.Col([
                                _tip("Slice index", ids.TOOLTIP_SLICE_INDEX, tip_text="Index of the slice to view."),
                                dcc.Slider(id=ids.GEOMETRY_SLICE_INDEX, min=0, max=1,
                                           step=1, value=0, marks=None,
                                           tooltip={"placement": "bottom", "always_visible": True}),
                            ], width=9),
                        ], className="mb-4"),
                        dcc.Graph(id=ids.GEOMETRY_SLICE, style={"height": "400px"}),
                    ]),
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
                            _tip("nproc [px, py, pz]", ids.TOOLTIP_NPROC, tip_text="Number of processors (GPUs) to use in each dimension."),
                            dbc.Input(id=ids.DOMAIN_NPROC, type="text",
                                      value="1, 1, 1",
                                      placeholder="1, 1, 1"),
                            html.Small("Process grid (e.g. 1, 1, 4).", className="text-muted"),
                        ], width=4),
                        dbc.Col([
                            _tip("n (subdomain) [nx, ny, nz]", ids.TOOLTIP_N_SUBDOM, tip_text="Dimensions of each subdomain. Must satisfy n[i] × nproc[i] ≤ N[i].\nDefaults to N[i]//nproc[i]."),
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
                            _tip("voxel_length", ids.TOOLTIP_VOXLEN, tip_text="Physical length represented by each voxel (in microns per voxel)."),
                            dbc.Input(id=ids.DOMAIN_VOXLEN, type="number",
                                      value=1.0, min=0, step=0.001),
                        ], width=3),
                    ], className="mb-2"),

                    dbc.Row([
                        dbc.Col([
                            _tip("ReadValues (from image)", ids.TOOLTIP_READ_VALUES, tip_text="Original image labels specified in the geometry file."),
                            dbc.Input(id=ids.DOMAIN_READ_VALUES, type="text", placeholder="0, 1"),
                            html.Div(id=ids.DOMAIN_READ_VALUES_DISPLAY),
                        ], width=4),
                        dbc.Col([
                            _tip("WriteValues (LBPM labels)", ids.TOOLTIP_WRITE_VALUES, tip_text="Labels corresponding 1:1 with ReadValues for relabeling. In LBPM convention:\nvalues ≤ 0 indicate solid\nvalues > 0 indicate fluid.\nFor multi-phase simulations:\n1 = nonwetting fluid;\n2 = wetting fluid."),
                            dbc.Input(id=ids.DOMAIN_WRITE_VALUES, type="text",
                                      placeholder="e.g. 0, 1"),
                            html.Small("Auto-derived from ReadValues; edit if needed.", className="text-muted"),
                        ], width=4),
                        dbc.Col([
                            _tip("ComponentLabels", ids.TOOLTIP_COMPONENT_LABELS, tip_text="Comma separated list of solid mineral labels"),
                            dbc.Input(id=ids.DOMAIN_COMPONENT_LABELS, type="text",
                                      placeholder="auto from WriteValues ≤ 0"),
                            html.Small("Auto-derived from WriteValues; edit if needed.", className="text-muted"),
                        ], width=4),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            _tip("Filename (geometry file)", ids.TOOLTIP_FILENAME, tip_text="Name of the geometry file."),
                            dbc.Input(id=ids.DOMAIN_FILENAME, type="text",
                                      placeholder="e.g. geometry.raw"),
                            html.Small("Auto-populated from path; edit if needed.", className="text-muted"),
                        ], width=6),
                        dbc.Col([
                            _tip("offset", ids.TOOLTIP_OFFSET, tip_text="Starting voxel offset into the file (default 0)."),
                            dbc.Input(id=ids.DOMAIN_OFFSET, type="number",
                                      value=0, min=0, step=1),
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
                            _tip("Simulation model", ids.TOOLTIP_MODEL_SELECTOR, tip_text="Select a simulation model from the dropdown."),
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
                        dbc.Col([
                            _tip("Protocol", ids.TOOLTIP_PROTOCOL, tip_text="Simulation protocols set up specific parameters for common computational experiments. The selected protocol will determine the boundary condition and set default simulation parameters; edit these parameters as needed."),
                            dbc.Select(
                                id=ids.COLOR_PROTOCOL,
                                options=[
                                    {"label": "fractional flow", "value": "fractional flow"},
                                    {"label": "core flooding", "value": "core flooding"},
                                    {"label": "centrifuge", "value": "centrifuge"},
                                    {"label": "image sequence", "value": "image sequence"},
                                    {"label": "shell aggregation", "value": "shell aggregation"},
                                    {"label": "None", "value": "None"},
                                ],
                                value="None",
                            ),
                        ], id="protocol-model-col", width=4),
                    ], className="mb-3"),

                    html.Hr(),

                    # Boundary condition + body force
                    html.H5("Boundary Settings"),
                    html.Small("Note that LBPM orients flow in the +Z direction.", className="text-muted"),
                    dbc.Row([
                        dbc.Col([
                            _tip("Boundary condition", ids.TOOLTIP_BC, tip_text="Boundary condition type. Periodic BCs are recommended for most cases."),
                            dbc.Select(
                                id=ids.DOMAIN_BC,
                                options=[
                                    {"label": "0 — Periodic", "value": "0"},
                                    {"label": "3 — Constant pressure", "value": "3"},
                                    {"label": "4 — Constant volumetric flux", "value": "4"},
                                ],
                                value="0",
                            ),
                        ], width=3),
                        dbc.Col([
                            _tip("Fx", ids.TOOLTIP_FX, tip_text="Uniform body force in the X direction."),
                            dbc.Input(id=ids.FLOW_F_X, type="number", value=0.0, step="any"),
                        ], width=2),
                        dbc.Col([
                            _tip("Fy", ids.TOOLTIP_FY, tip_text="Uniform body force in the Y direction."),
                            dbc.Input(id=ids.FLOW_F_Y, type="number", value=0.0, step="any"),
                        ], width=2),
                        dbc.Col([
                            _tip("Fz", ids.TOOLTIP_FZ, tip_text="Uniform body force in the Z direction."),
                            dbc.Input(id=ids.FLOW_F_Z, type="number", value=1e-5, step="any"),
                        ], width=2),
                    ], className="mb-2"),
                    html.Div(id=ids.DOMAIN_BC_PARAMS, children=[
                        dbc.Row(id="bc-pressure-row", style={"display": "none"}, children=[
                            dbc.Col([
                                _tip("din", ids.TOOLTIP_DIN, tip_text="Density at the inlet."),
                                dbc.Input(id=ids.DOMAIN_DIN, type="number", value=1.0, step=0.001),
                            ], width=3),
                            dbc.Col([
                                _tip("dout", ids.TOOLTIP_DOUT, tip_text="Density at the outlet."),
                                dbc.Input(id=ids.DOMAIN_DOUT, type="number", value=1.0, step=0.001),
                            ], width=3),
                        ], className="mb-3"),
                        dbc.Row(id="bc-flux-row", style={"display": "none"}, children=[
                            dbc.Col([
                                _tip("flux", ids.TOOLTIP_FLUX, tip_text="Volumetric flux (voxels per timestep)"),
                                dbc.Input(id=ids.DOMAIN_FLUX, type="number", value=0.0, step=0.0001),
                            ], width=3),
                        ], className="mb-3"),
                    ]),

                    # Inlet/Outlet layers and phases (shown for all models)
                    dbc.Row([
                        dbc.Col([_tip("inletLayers [x,y,z]", ids.TOOLTIP_INLET_LAYERS, tip_text="Number of mixing layers at the inlet"), dbc.Input(id=ids.DOMAIN_INLET_LAYERS, type="text", value="0, 0, 5")], width=3),
                        dbc.Col([_tip("outletLayers [x,y,z]", ids.TOOLTIP_OUTLET_LAYERS, tip_text="Number of mixing layers at the outlet"), dbc.Input(id=ids.DOMAIN_OUTLET_LAYERS, type="text", value="0, 0, 5")], width=3),
                        dbc.Col([_tip("InletLayersPhase", ids.TOOLTIP_INLET_LAYERS_PHASE, tip_text="Phase label for inlet mixing (default 2: wetting fluid)"), dbc.Input(id=ids.DOMAIN_INLET_LAYERS_PHASE, type="number", value=2, step=1)], width=3),
                        dbc.Col([_tip("OutletLayersPhase", ids.TOOLTIP_OUTLET_LAYERS_PHASE, tip_text="Phase label for outlet mixing (default 1: non-wetting fluid)"), dbc.Input(id=ids.DOMAIN_OUTLET_LAYERS_PHASE, type="number", value=1, step=1)], width=3),
                    ], className="mb-3"),

                    html.Hr(),

                    # Color model params
                    html.Div(id="color-params", children=[
                        html.H5("Color Model Parameters"),
                        dbc.Row([
                            dbc.Col([_tip("tauA", ids.TOOLTIP_TAU_A, tip_text="Relaxation time for component A — controls fluid viscosity\n(0.7 < tauA < 1.5)."), dbc.Input(id=ids.COLOR_TAU_A, type="number", value=0.7, step=0.01)], width=2),
                            dbc.Col([_tip("tauB", ids.TOOLTIP_TAU_B, tip_text="Relaxation time for component B — controls fluid viscosity\n(0.7 < tauB < 1.5)."), dbc.Input(id=ids.COLOR_TAU_B, type="number", value=0.7, step=0.01)], width=2),
                            dbc.Col([_tip("rhoA", ids.TOOLTIP_RHO_A, tip_text="Controls density for component A\n(0.05 < rhoA < 1.0)."), dbc.Input(id=ids.COLOR_RHO_A, type="number", value=1.0, step=0.01)], width=2),
                            dbc.Col([_tip("rhoB", ids.TOOLTIP_RHO_B, tip_text="Controls density for component B\n(0.05 < rhoB < 1.0)."), dbc.Input(id=ids.COLOR_RHO_B, type="number", value=1.0, step=0.01)], width=2),
                            dbc.Col([_tip("alpha", ids.TOOLTIP_ALPHA, tip_text="Controls interfacial tension\n(0 < alpha < 1)."), dbc.Input(id=ids.COLOR_ALPHA, type="number", value=0.01, step=0.001)], width=2),
                            dbc.Col([_tip("beta", ids.TOOLTIP_BETA, tip_text="Controls interface width\n(beta < 1)."), dbc.Input(id=ids.COLOR_BETA, type="number", value=0.95, step=0.01)], width=2),
                        ], className="mb-2"),
                        dbc.Row([
                            dbc.Col([_tip("capillary_number", ids.TOOLTIP_CAP_NUM, tip_text="Target capillary number for the displacement"), dbc.Input(id=ids.COLOR_CAP_NUM, type="number", value=1e-5, step=1e-6)], id="cap-num-col", width=3),
                            dbc.Col([_tip("timestepMax", ids.TOOLTIP_TIMESTEP_MAX, tip_text="Maximum number of timesteps for the simulation"), dbc.Input(id=ids.COLOR_TIMESTEP_MAX, type="number", value=10000000, step=1000)], width=3),
                            dbc.Col([
                                _tip("Restart", ids.TOOLTIP_RESTART, tip_text="Enable to restart from previous simulation state. Requires a valid restart file."),
                                dbc.Checklist(id=ids.COLOR_RESTART,
                                              options=[{"label": "Restart", "value": "true"}],
                                              value=[]),
                            ], width=3),
                        ], className="mb-2"),
                        dbc.Row([
                            dbc.Col([
                                _tip("ComponentAffinity (wetting per solid label)", ids.TOOLTIP_COMPONENT_AFFINITY, tip_text="Wetting affinity for each solid label corresponding to ComponentLabels (~cos(wetting angle))"),
                                dbc.Input(id=ids.COLOR_COMPONENT_AFFINITY, type="text",
                                          placeholder="e.g. 1.0  (one value per ComponentLabel)"),
                            ], width=6),
                        ], className="mb-2"),

                        # FlowAdaptor
                        html.Div(id="flow-adaptor-section", style={"display": "none"}, children=[
                            html.H6("FlowAdaptor (fractional flow control)", className="mt-3"),
                            dbc.Row([
                                dbc.Col([_tip("max_steady_timesteps", ids.TOOLTIP_FA_MAX_STEADY, tip_text="Maximum number of timesteps per steady point"), dbc.Input(id=ids.FA_MAX_STEADY, type="number", value=1000000, step=1000)], width=3),
                                dbc.Col([_tip("min_steady_timesteps", ids.TOOLTIP_FA_MIN_STEADY, tip_text="Minimum number of timesteps per steady point"), dbc.Input(id=ids.FA_MIN_STEADY, type="number", value=1000000, step=1000)], width=3),
                                dbc.Col([_tip("fractional_flow_increment", ids.TOOLTIP_FA_FF_INCREMENT, tip_text="Target change in saturation between steady points"), dbc.Input(id=ids.FA_FF_INCREMENT, type="number", value=0.05, step=0.01)], width=3),
                                dbc.Col([_tip("skip_timesteps", ids.TOOLTIP_FA_SKIP_TIMESTEPS, tip_text="Timesteps to spend in adaptive part of algorithm"), dbc.Input(id=ids.FA_SKIP_TIMESTEPS, type="number", value=50000, step=1000)], width=3),
                            ], className="mb-2"),
                            dbc.Row([
                                dbc.Col([_tip("endpoint_threshold", ids.TOOLTIP_FA_ENDPOINT_THRESH, tip_text="Termination criterion based on the relative flow rates of fluids."), dbc.Input(id=ids.FA_ENDPOINT_THRESH, type="number", value=0.1, step=0.01)], width=3),
                                dbc.Col([_tip("mass_fraction_factor", ids.TOOLTIP_FA_MASS_FRACTION, tip_text="Controls the rate of mass seeding in adaptive step.\nIf value > 0, the algorithm will remove mass from fluid A and add mass to fluid B. Vice versa if value < 0."), dbc.Input(id=ids.FA_MASS_FRACTION, type="number", value=0.006, step=0.0001)], width=3),
                                dbc.Col([_tip("fractional_flow_epsilon", ids.TOOLTIP_FA_FF_EPSILON, tip_text="Controls the threshold velocity to minimize influence of spurious currents"), dbc.Input(id=ids.FA_FF_EPSILON, type="number", value=5e-6, step=1e-7)], width=3),
                            ]),
                        ]),
                    ]),

                    # Permeability model params (hidden by default)
                    html.Div(id="perm-params", style={"display": "none"}, children=[
                        html.H5("Permeability Model Parameters"),
                        dbc.Row([
                            dbc.Col([_tip("tau", ids.TOOLTIP_PERM_TAU, tip_text="Relaxation time — controls fluid viscosity\n0.7 < tau < 1.5"), dbc.Input(id="perm-tau", type="number", value=1.0, step=0.01)], width=3),
                            dbc.Col([_tip("tolerance", ids.TOOLTIP_PERM_TOLERANCE, tip_text="Convergence tolerance (relative difference in flow rate)"), dbc.Input(id="perm-tolerance", type="number", value=1e-8, step=1e-9)], width=3),
                            dbc.Col([_tip("timestepMax", ids.TOOLTIP_PERM_TIMESTEP_MAX, tip_text="Maximum number of timesteps"), dbc.Input(id="perm-timestep-max", type="number", value=100000, step=1000)], width=3),
                        ]),
                    ]),

                    # Morphology model params (hidden by default)
                    html.Div(id="morph-params", style={"display": "none"}, children=[
                        html.H5("Morphology Parameters"),
                        dbc.Row([
                            dbc.Col([
                                _tip("Operation", ids.TOOLTIP_MORPH_OPERATION, tip_text="Initialize fluid configurations based on the chosen morphological operation."),
                                dbc.RadioItems(
                                    id="morph-operation",
                                    options=[
                                        {"label": "Drainage", "value": "drainage"},
                                        {"label": "Opening", "value": "opening"},
                                    ],
                                    value="drainage",
                                    inline=True,
                                ),
                            ], width=6),
                            dbc.Col([
                                _tip("Target saturation (Sw)", ids.TOOLTIP_MORPH_SW,
                                     tip_text="Target wetting-phase saturation for morphological operation\n(0 < Sw <1)."),
                                dbc.Input(id=ids.MORPH_SW, type="number", value=0.5,
                                          min=0.0, max=1.0, step=0.01),
                            ], width=3),
                        ]),
                    ]),

                    html.Hr(),

                    # Analysis section (all models)
                    html.H5("Analysis Settings"),
                    dbc.Row([
                        dbc.Col([_tip("analysis_interval", ids.TOOLTIP_ANALYSIS_INTERVAL, tip_text="Logging interval for timelog.csv"), dbc.Input(id=ids.ANALYSIS_INTERVAL, type="number", value=1000, step=100)], width=3),
                        dbc.Col([_tip("subphase_analysis_interval", ids.TOOLTIP_SUBPHASE_INTERVAL, tip_text="Logging interval for subphase.csv"), dbc.Input(id=ids.ANALYSIS_SUBPHASE_INTERVAL, type="number", value=5000, step=100)], width=3),
                        dbc.Col([_tip("visualization_interval", ids.TOOLTIP_VIS_INTERVAL, tip_text="Interval to write visualization files"), dbc.Input(id=ids.ANALYSIS_VIS_INTERVAL, type="number", value=10000, step=1000)], width=3),
                        dbc.Col([_tip("N_threads", ids.TOOLTIP_N_THREADS, tip_text="Number of analysis threads (GPU version only)"), dbc.Input(id=ids.ANALYSIS_N_THREADS, type="number", value=4, min=1, step=1)], width=3),
                    ], className="mb-2"),
                    dbc.Row([
                        dbc.Col([
                            _tip("restart_file", ids.TOOLTIP_RESTART_FILENAME, tip_text="Base name of the restart file."),
                            dbc.Input(id=ids.ANALYSIS_RESTART_FILENAME, type="text",
                                      value="Restart"),], width=6),
                        dbc.Col([_tip("restart_interval", ids.TOOLTIP_RESTART_INTERVAL, tip_text="Interval to write restart files"), dbc.Input(id=ids.ANALYSIS_RESTART_INTERVAL, type="number", value=1000000, step=100000)], width=3),

                    ], className="mb-3"),

                    html.Hr(),

                    html.H5("Visualization Settings"),

                    dbc.Row([
                        dbc.Col([
                            _tip("save_8bit_raw", ids.TOOLTIP_SAVE_8BIT, tip_text="Enable to save phase configurations as 8-bit raw files for visualization."),
                            dbc.Checklist(
                                id=ids.VIS_SAVE_8BIT,
                                options=[{"label": "Enabled", "value": "true"}],
                                value=["true"],
                            ),
                        ], width=3),
                        dbc.Col([
                            _tip("save_phase_field", ids.TOOLTIP_SAVE_PHASE, tip_text="Enable to save phase field within SILO database."),
                            dbc.Checklist(
                                id=ids.VIS_SAVE_PHASE,
                                options=[{"label": "Enabled", "value": "true"}],
                                value=["true"],
                            ),
                        ], width=3),
                        dbc.Col([
                            _tip("save_pressure_field", ids.TOOLTIP_SAVE_PRESSURE, tip_text="Enable to save pressure field within SILO database."),
                            dbc.Checklist(
                                id=ids.VIS_SAVE_PRESSURE,
                                options=[{"label": "Enabled", "value": "true"}],
                                value=["true"],
                            ),
                        ], width=3),
                        dbc.Col([
                            _tip("save_velocity_field", ids.TOOLTIP_SAVE_VELOCITY, tip_text="Enable to save velocity field within SILO database."),
                            dbc.Checklist(
                                id=ids.VIS_SAVE_VELOCITY,
                                options=[{"label": "Enabled", "value": "true"}],
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
                            _tip("Remote base path", ids.TOOLTIP_REMOTE_BASE_PATH, tip_text="Base path where the simulation directory will be created."),
                            dbc.Input(id=ids.REMOTE_BASE_PATH, type="text",
                                      placeholder="/scratch/user/simulations"),
                        ], width=6),
                        dbc.Col([
                            _tip("Simulation directory name", ids.TOOLTIP_SIM_NAME, tip_text="Name of the simulation directory to create within the base path."),
                            dbc.Input(id=ids.SIM_NAME_INPUT, type="text",
                                      placeholder="e.g. berea_color_run1"),
                        ], width=4),
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Preview input.db", id=ids.PREVIEW_INPUT_DB_BTN,
                                       color="light", className="me-2"),
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
        # Autosave interval — page-scoped so it only fires when Geometry Setup is mounted
        dcc.Interval(id=ids.GEOMETRY_AUTOSAVE_INTERVAL, interval=1000, n_intervals=0),
    ],
)


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@callback(
    Output("geometry-path-row", "style"),
    Output("geometry-upload-row", "style"),
    Output("geometry-dims-row", "style"),
    Input(ids.GEOMETRY_SOURCE_RADIO, "value"),
)
def toggle_source(source):
    show, hide = {}, {"display": "none"}
    if source == "path":
        return show, hide, hide
    if source == "upload":
        return hide, show, hide
    # dims
    return hide, hide, show


@callback(
    Output(ids.GEOMETRY_INFO, "children"),
    Output(ids.GEOMETRY_SLICE_INDEX, "max"),
    Output(ids.GEOMETRY_SLICE_INDEX, "value"),
    Output(ids.GEOMETRY_ARRAY_STORE, "data"),
    Output(ids.DOMAIN_READ_VALUES_DISPLAY, "children"),
    Output(ids.DOMAIN_READ_VALUES, "value"),
    Output(ids.DOMAIN_WRITE_VALUES, "value"),
    Output(ids.DOMAIN_COMPONENT_LABELS, "value"),
    Output(ids.DOMAIN_N_SUBDOM, "value"),
    Output(ids.GEOMETRY_SLICE_VIEWER, "style"),
    Input(ids.GEOMETRY_LOAD_BTN, "n_clicks"),
    State(ids.GEOMETRY_SOURCE_RADIO, "value"),
    State(ids.GEOMETRY_REMOTE_PATH, "value"),
    State(ids.GEOMETRY_UPLOAD, "contents"),
    State(ids.GEOMETRY_NX, "value"),
    State(ids.GEOMETRY_NY, "value"),
    State(ids.GEOMETRY_NZ, "value"),
    State(ids.DOMAIN_NPROC, "value"),
    State(ids.MODEL_SELECTOR, "value"),
    prevent_initial_call=True,
)
def load_geometry(n_clicks, source, remote_path, upload_contents, nx, ny, nz, nproc_str, model):
    if not nx or not ny or not nz:
        return (
            dbc.Alert("Please enter Nx, Ny, Nz before loading.", color="danger"),
            1, 0, None,
            None,
            "", "", "", "",
            {"display": "none"},
        )

    nx, ny, nz = int(nx), int(ny), int(nz)

    # Dims-only mode: no file, just set defaults from model
    if source == "dims":
        try:
            nproc = [int(x.strip()) for x in nproc_str.split(",")]
        except Exception:
            nproc = [1, 1, 1]
        n_sub = [nx // nproc[0], ny // nproc[1], nz // nproc[2]]
        n_sub_str = ", ".join(str(v) for v in n_sub)
        if model == "perm":
            read_write = "0, 1"
            comp = ""
        else:
            read_write = "0, 1, 2"
            comp = "0"
        info = dbc.Alert(
            [html.B("Dimensions set. "),
             f"Shape: {nx}×{ny}×{nz} — no geometry file loaded."],
            color="success",
        )
        return (
            info,
            nz - 1, nz // 2,
            None,
            html.Small("No geometry file — labels set to defaults.", className="text-muted"),
            read_write,
            read_write,
            comp,
            n_sub_str,
            {"display": "none"},
        )

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

        arr = np.frombuffer(raw_bytes, dtype=np.uint8).reshape(nz, ny, nx)
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

        store_data = {
            "nx": nx, "ny": ny, "nz": nz,
            "b64": base64.b64encode(raw_bytes).decode(),
        }

        return (
            info,
            nz - 1, nz // 2,
            store_data,
            html.Div([
                "Found labels ",
                html.Code(labels_str),
                " from loaded file",
            ]),
            labels_str,
            write_values_default,
            component_labels_default,
            n_sub_str,
            {},
        )

    except Exception as e:
        return (
            dbc.Alert(f"Error loading geometry: {e}", color="danger"),
            1, 0, None,
            None,
            "", "", "", "",
            {"display": "none"},
        )


@callback(
    Output(ids.GEOMETRY_SLICE, "figure"),
    Input(ids.GEOMETRY_SLICE_AXIS, "value"),
    Input(ids.GEOMETRY_SLICE_INDEX, "value"),
    State(ids.GEOMETRY_ARRAY_STORE, "data"),
    prevent_initial_call=True,
)
def update_slice(axis_str, slice_idx, store_data):
    if not store_data:
        return {}
    axis = int(axis_str)
    nx, ny, nz = store_data["nx"], store_data["ny"], store_data["nz"]
    raw_bytes = base64.b64decode(store_data["b64"])

    # Memory layout: C-order (nz, ny, nx) — Z is dim 0 (outermost), X is dim 2 (fastest)
    axis_labels = ["Z", "Y", "X"]
    if axis == 0:
        # Z-slice: contiguous block — read only needed bytes via offset
        offset = slice_idx * ny * nx
        s = np.frombuffer(raw_bytes, dtype=np.uint8, offset=offset, count=ny * nx).reshape(ny, nx)
        xlabel, ylabel = "X", "Y"
    elif axis == 1:
        # Y-slice: one row per Z-layer
        flat = np.frombuffer(raw_bytes, dtype=np.uint8)
        s = flat.reshape(nz, ny * nx)[:, slice_idx * nx:(slice_idx + 1) * nx].reshape(nz, nx)
        xlabel, ylabel = "X", "Z"
    else:
        # X-slice: one column per row in every Z-layer
        flat = np.frombuffer(raw_bytes, dtype=np.uint8)
        s = flat.reshape(nz * ny, nx)[:, slice_idx].reshape(nz, ny)
        xlabel, ylabel = "Y", "Z"

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
    Output(ids.DOMAIN_N_SUBDOM, "value", allow_duplicate=True),
    Input(ids.DOMAIN_NPROC, "value"),
    State(ids.GEOMETRY_NX, "value"),
    State(ids.GEOMETRY_NY, "value"),
    State(ids.GEOMETRY_NZ, "value"),
    State(ids.DOMAIN_N_SUBDOM, "value"),
    prevent_initial_call=True,
)
def auto_n_subdom(nproc_str, nx, ny, nz, current_n_subdom):
    # Preserve manual edits — only auto-compute when field is empty or shows placeholder
    _placeholder = "auto-computed from N / proc"
    if current_n_subdom and current_n_subdom != _placeholder:
        return dash.no_update
    if not nx or not ny or not nz or not nproc_str:
        return _placeholder
    try:
        N = [int(nx), int(ny), int(nz)]
        nproc = [int(x.strip()) for x in nproc_str.split(",")]
        n_sub = [N[i] // nproc[i] for i in range(3)]
        return ", ".join(str(v) for v in n_sub)
    except Exception:
        return _placeholder

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
    State(ids.DOMAIN_FILENAME, "value"),
    prevent_initial_call=True,
)
def auto_filename(remote_path, current_filename):
    if not remote_path:
        return dash.no_update
    # Only auto-fill filename if the user hasn't manually edited it
    if current_filename:
        return dash.no_update
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
    Output("protocol-model-col", "style"),
    Input(ids.MODEL_SELECTOR, "value"),
)
def toggle_model_params(model):
    show = {}
    hide = {"display": "none"}
    return (
        show if model == "color" else hide,
        show if model == "perm" else hide,
        show if model == "morph" else hide,
        show if model == "color" else hide,
    )


_PROTOCOL_BC = {
    "fractional flow": "0",
    "core flooding": "4",
    "centrifuge": "3",
    "image sequence": "0",
    "shell aggregation": "0",
    "None": "0",
}

_PROTOCOL_BC_DISABLED = {
    "fractional flow": True,
    "core flooding": True,
    "centrifuge": True,
    "image sequence": False,
    "shell aggregation": True,
    "None": False,
}

@callback(
    Output(ids.DOMAIN_BC, "value", allow_duplicate=True),
    Output(ids.DOMAIN_BC, "disabled"),
    Output("flow-adaptor-section", "style"),
    Output("cap-num-col", "style"),
    Input(ids.COLOR_PROTOCOL, "value"),
    State(ids.MODEL_SELECTOR, "value"),
    prevent_initial_call=True,
)
def update_protocol_bc(protocol, model):
    if model != "color":
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    show, hide = {}, {"display": "none"}
    disabled = _PROTOCOL_BC_DISABLED.get(protocol or "None", False)
    # When protocol is None/image sequence (user-editable BC), don't override BC value
    if protocol in (None, "None", "image sequence"):
        bc = dash.no_update
    else:
        bc = _PROTOCOL_BC.get(protocol, "0")
    show_fa = show if protocol in ("None", "image sequence", "fractional flow") else hide
    show_cap = show if protocol not in ("core flooding", "centrifuge") else hide
    return bc, disabled, show_fa, show_cap


# ---------------------------------------------------------------------------
# Session persistence: save all form fields on any change
# ---------------------------------------------------------------------------

@callback(
    Output(ids.GEOMETRY_SESSION_STORE, "data"),
    Input(ids.GEOMETRY_AUTOSAVE_INTERVAL, "n_intervals"),
    State(ids.GEOMETRY_NX, "value"),
    State(ids.GEOMETRY_NY, "value"),
    State(ids.GEOMETRY_NZ, "value"),
    State(ids.GEOMETRY_REMOTE_PATH, "value"),
    State(ids.GEOMETRY_SOURCE_RADIO, "value"),
    State(ids.FLOW_F_X, "value"),
    State(ids.FLOW_F_Y, "value"),
    State(ids.FLOW_F_Z, "value"),
    State(ids.GEOMETRY_SLICE_AXIS, "value"),
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
    State(ids.DOMAIN_INLET_LAYERS, "value"),
    State(ids.DOMAIN_OUTLET_LAYERS, "value"),
    State(ids.DOMAIN_INLET_LAYERS_PHASE, "value"),
    State(ids.DOMAIN_OUTLET_LAYERS_PHASE, "value"),
    State(ids.COLOR_COMPONENT_AFFINITY, "value"),
    State(ids.FA_MAX_STEADY, "value"),
    State(ids.FA_MIN_STEADY, "value"),
    State(ids.FA_FF_INCREMENT, "value"),
    State(ids.FA_MASS_FRACTION, "value"),
    State(ids.FA_ENDPOINT_THRESH, "value"),
    State(ids.FA_FF_EPSILON, "value"),
    State(ids.FA_SKIP_TIMESTEPS, "value"),
    State(ids.ANALYSIS_INTERVAL, "value"),
    State(ids.ANALYSIS_SUBPHASE_INTERVAL, "value"),
    State(ids.ANALYSIS_VIS_INTERVAL, "value"),
    State(ids.ANALYSIS_N_THREADS, "value"),
    State(ids.ANALYSIS_RESTART_INTERVAL, "value"),
    State(ids.ANALYSIS_RESTART_FILENAME, "value"),
    State(ids.VIS_SAVE_8BIT, "value"),
    State(ids.VIS_SAVE_PHASE, "value"),
    State(ids.VIS_SAVE_PRESSURE, "value"),
    State(ids.VIS_SAVE_VELOCITY, "value"),
    State(ids.REMOTE_BASE_PATH, "value"),
    State(ids.SIM_NAME_INPUT, "value"),
    State(ids.MORPH_SW, "value"),
)
def save_session(_n_intervals, nx, ny, nz, remote_path, source, fx, fy, fz, slice_axis,
                 nproc, n_subdom, voxlen, bc, din, dout, flux,
                 read_values, write_values, component_labels, filename, offset,
                 model, tau_a, tau_b, rho_a, rho_b, alpha, beta, cap_num, timestep_max,
                 restart, protocol, inlet_layers, outlet_layers, inlet_layers_phase, outlet_layers_phase, affinity,
                 fa_max, fa_min, fa_incr, fa_mass, fa_ep, fa_epsilon, fa_skip_timesteps,
                 analysis_interval, subphase_interval, vis_interval, n_threads, restart_interval, restart_filename,
                 save_8bit, save_phase, save_pressure, save_velocity,
                 base_path, sim_name, morph_sw):
    return {
        "nx": nx, "ny": ny, "nz": nz,
        "remote_path": remote_path, "source": source,
        "fx": fx, "fy": fy, "fz": fz, "slice_axis": slice_axis,
        "nproc": nproc, "n_subdom": n_subdom, "voxlen": voxlen,
        "bc": bc, "din": din, "dout": dout, "flux": flux,
        "read_values": read_values, "write_values": write_values,
        "component_labels": component_labels, "filename": filename, "offset": offset,
        "model": model,
        "tau_a": tau_a, "tau_b": tau_b, "rho_a": rho_a, "rho_b": rho_b,
        "alpha": alpha, "beta": beta, "cap_num": cap_num, "timestep_max": timestep_max,
        "restart": restart, "protocol": protocol,
        "inlet_layers": inlet_layers, "outlet_layers": outlet_layers,
        "inlet_layers_phase": inlet_layers_phase, "outlet_layers_phase": outlet_layers_phase,
        "affinity": affinity,
        "fa_max": fa_max, "fa_min": fa_min, "fa_incr": fa_incr,
        "fa_mass": fa_mass, "fa_ep": fa_ep, "fa_epsilon": fa_epsilon, "fa_skip_timesteps": fa_skip_timesteps,
        "analysis_interval": analysis_interval, "subphase_interval": subphase_interval,
        "vis_interval": vis_interval, "n_threads": n_threads,
        "restart_interval": restart_interval, "restart_filename": restart_filename,
        "save_8bit": save_8bit, "save_phase": save_phase,
        "save_pressure": save_pressure, "save_velocity": save_velocity,
        "base_path": base_path, "sim_name": sim_name,
        "morph_sw": morph_sw,
    }


@callback(
    Output(ids.GEOMETRY_NX, "value"),
    Output(ids.GEOMETRY_NY, "value"),
    Output(ids.GEOMETRY_NZ, "value"),
    Output(ids.GEOMETRY_REMOTE_PATH, "value"),
    Output(ids.GEOMETRY_SOURCE_RADIO, "value"),
    Output(ids.FLOW_F_X, "value"),
    Output(ids.FLOW_F_Y, "value"),
    Output(ids.FLOW_F_Z, "value"),
    Output(ids.GEOMETRY_SLICE_AXIS, "value"),
    Output(ids.DOMAIN_NPROC, "value"),
    Output(ids.DOMAIN_N_SUBDOM, "value", allow_duplicate=True),
    Output(ids.DOMAIN_VOXLEN, "value"),
    Output(ids.DOMAIN_BC, "value"),
    Output(ids.DOMAIN_DIN, "value"),
    Output(ids.DOMAIN_DOUT, "value"),
    Output(ids.DOMAIN_FLUX, "value"),
    Output(ids.DOMAIN_WRITE_VALUES, "value", allow_duplicate=True),
    Output(ids.DOMAIN_COMPONENT_LABELS, "value", allow_duplicate=True),
    Output(ids.DOMAIN_FILENAME, "value", allow_duplicate=True),
    Output(ids.DOMAIN_OFFSET, "value"),
    Output(ids.MODEL_SELECTOR, "value"),
    Output(ids.COLOR_TAU_A, "value"),
    Output(ids.COLOR_TAU_B, "value"),
    Output(ids.COLOR_RHO_A, "value"),
    Output(ids.COLOR_RHO_B, "value"),
    Output(ids.COLOR_ALPHA, "value"),
    Output(ids.COLOR_BETA, "value"),
    Output(ids.COLOR_CAP_NUM, "value"),
    Output(ids.COLOR_TIMESTEP_MAX, "value"),
    Output(ids.COLOR_RESTART, "value"),
    Output(ids.COLOR_PROTOCOL, "value"),
    Output(ids.DOMAIN_INLET_LAYERS, "value"),
    Output(ids.DOMAIN_OUTLET_LAYERS, "value"),
    Output(ids.DOMAIN_INLET_LAYERS_PHASE, "value"),
    Output(ids.DOMAIN_OUTLET_LAYERS_PHASE, "value"),
    Output(ids.COLOR_COMPONENT_AFFINITY, "value"),
    Output(ids.FA_MAX_STEADY, "value"),
    Output(ids.FA_MIN_STEADY, "value"),
    Output(ids.FA_FF_INCREMENT, "value"),
    Output(ids.FA_MASS_FRACTION, "value"),
    Output(ids.FA_ENDPOINT_THRESH, "value"),
    Output(ids.FA_FF_EPSILON, "value"),
    Output(ids.FA_SKIP_TIMESTEPS, "value"),
    Output(ids.ANALYSIS_INTERVAL, "value"),
    Output(ids.ANALYSIS_SUBPHASE_INTERVAL, "value"),
    Output(ids.ANALYSIS_VIS_INTERVAL, "value"),
    Output(ids.ANALYSIS_N_THREADS, "value"),
    Output(ids.ANALYSIS_RESTART_INTERVAL, "value"),
    Output(ids.ANALYSIS_RESTART_FILENAME, "value"),
    Output(ids.VIS_SAVE_8BIT, "value"),
    Output(ids.VIS_SAVE_PHASE, "value"),
    Output(ids.VIS_SAVE_PRESSURE, "value"),
    Output(ids.VIS_SAVE_VELOCITY, "value"),
    Output(ids.REMOTE_BASE_PATH, "value"),
    Output(ids.SIM_NAME_INPUT, "value"),
    Output(ids.MORPH_SW, "value"),
    Input(ids.GEOMETRY_SESSION_STORE, "data"),
    prevent_initial_call=True,
)
def restore_session(data):
    if not data:
        return (dash.no_update,) * 53
    d = data
    return (
        d.get("nx"), d.get("ny"), d.get("nz"),
        d.get("remote_path"), d.get("source", "path"),
        d.get("fx", 0.0), d.get("fy", 0.0), d.get("fz", 1e-5),
        d.get("slice_axis", "2"),
        d.get("nproc", "1, 1, 1"), d.get("n_subdom"),
        d.get("voxlen", 1.0), d.get("bc", "0"),
        d.get("din", 1.0), d.get("dout", 1.0), d.get("flux", 0.0),
        d.get("write_values"), d.get("component_labels"),
        d.get("filename"), d.get("offset", 0),
        d.get("model", "color"),
        d.get("tau_a", 0.7), d.get("tau_b", 0.7),
        d.get("rho_a", 1.0), d.get("rho_b", 1.0),
        d.get("alpha", 0.01), d.get("beta", 0.95),
        d.get("cap_num", 1e-5), d.get("timestep_max", 10000000),
        d.get("restart", []), d.get("protocol", "None"),
        d.get("inlet_layers", "0, 0, 5"), d.get("outlet_layers", "0, 0, 5"),
        d.get("inlet_layers_phase", 2), d.get("outlet_layers_phase", 1),
        d.get("affinity"),
        d.get("fa_max", 200000), d.get("fa_min", 100000),
        d.get("fa_incr", 0.1), d.get("fa_mass", 0.0002), d.get("fa_ep", 0.1),
        d.get("fa_epsilon", 1e-6), d.get("fa_skip_timesteps", 0),
        d.get("analysis_interval", 1000), d.get("subphase_interval", 5000),
        d.get("vis_interval", 10000), d.get("n_threads", 4),
        d.get("restart_interval", 1000000),
        d.get("restart_filename", "Restart"),
        d.get("save_8bit", ["true"]), d.get("save_phase", ["true"]),
        d.get("save_pressure", ["true"]), d.get("save_velocity", ["true"]),
        d.get("base_path"), d.get("sim_name"),
        d.get("morph_sw", 0.5),
    )


# ---------------------------------------------------------------------------
# "Load New Geometry" — clear geometry-related fields only
# ---------------------------------------------------------------------------

@callback(
    Output(ids.GEOMETRY_ARRAY_STORE, "data", allow_duplicate=True),
    Output(ids.GEOMETRY_NX, "value", allow_duplicate=True),
    Output(ids.GEOMETRY_NY, "value", allow_duplicate=True),
    Output(ids.GEOMETRY_NZ, "value", allow_duplicate=True),
    Output(ids.GEOMETRY_REMOTE_PATH, "value", allow_duplicate=True),
    Output(ids.GEOMETRY_SLICE_INDEX, "max", allow_duplicate=True),
    Output(ids.GEOMETRY_SLICE_INDEX, "value", allow_duplicate=True),
    Output(ids.GEOMETRY_INFO, "children", allow_duplicate=True),
    Output(ids.DOMAIN_READ_VALUES, "value", allow_duplicate=True),
    Output(ids.DOMAIN_READ_VALUES_DISPLAY, "children", allow_duplicate=True),
    Output(ids.DOMAIN_WRITE_VALUES, "value", allow_duplicate=True),
    Output(ids.DOMAIN_COMPONENT_LABELS, "value", allow_duplicate=True),
    Output(ids.DOMAIN_N_SUBDOM, "value", allow_duplicate=True),
    Output(ids.DOMAIN_FILENAME, "value", allow_duplicate=True),
    Output(ids.GEOMETRY_SLICE_VIEWER, "style", allow_duplicate=True),
    Input(ids.LOAD_NEW_GEOMETRY_BTN, "n_clicks"),
    prevent_initial_call=True,
)
def reset_geometry(_):
    return (
        None,    # geometry array store
        None, None, None,  # Nx, Ny, Nz
        None,    # remote path
        1, 0,    # slice index max/value
        None,    # geometry info
        "",      # read values (hidden)
        None,    # read values display
        "",      # write values
        "",      # component labels
        "",      # n subdom
        "",      # filename
        {"display": "none"},
    )


# ---------------------------------------------------------------------------
# Build input.db helper
# ---------------------------------------------------------------------------

def _build_input_db(
    nx, ny, nz, nproc_str, n_sub_str, voxlen, bc,
    din, dout, flux,
    read_values_str, write_values_str, component_labels_str,
    filename, offset,
    model, f_x, f_y, f_z,
    tau_a, tau_b, rho_a, rho_b, alpha, beta, cap_num, timestep_max,
    restart, protocol, inlet_layers_str, outlet_layers_str, inlet_layers_phase, outlet_layers_phase, affinity_str,
    fa_max, fa_min, fa_incr, fa_mass, fa_ep, fa_skip, fa_ff_eps,
    perm_tau, perm_tolerance, perm_timestep_max,
    analysis_interval, subphase_interval, vis_interval, n_threads, restart_interval, restart_filename,
    save_8bit, save_phase, save_pressure, save_velocity,
    morph_sw=None,
):
    """Generate the full input.db text string from form values."""
    def parse_list(s):
        return [x.strip() for x in (s or "").split(",") if x.strip()]

    nproc = parse_list(nproc_str) or ["1", "1", "1"]
    n_sub = parse_list(n_sub_str) or [str(int(n) // int(p)) for p, n in zip(nproc, [nx, ny, nz])]
    read_vals = parse_list(read_values_str)
    write_vals = parse_list(write_values_str) or read_vals
    comp_labels = parse_list(component_labels_str)

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
    if model != "perm":
        db += f"   ComponentLabels = {', '.join(comp_labels)}\n"
    if protocol not in (None, "None"):
        db += f"   BC = {bc}\n"
        if str(bc) == "3":
            db += f"   din = {din if din is not None else 1.0}\n"
            db += f"   dout = {dout if dout is not None else 1.0}\n"
        elif str(bc) == "4":
            db += f"   flux = {flux if flux is not None else 0.0}\n"
    if model == "morph" and morph_sw is not None:
        db += f"   Sw = {morph_sw}\n"
    db += f"   InletLayersPhase = {inlet_layers_phase if inlet_layers_phase is not None else 2}\n"
    db += f"   OutletLayersPhase = {outlet_layers_phase if outlet_layers_phase is not None else 1}\n"
    db += "}\n\n"

    if model == "color":
        restart_val = "true" if "true" in (restart or []) else "false"
        db += "Color {\n"
        if protocol and protocol not in ("None", "user specified"):
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
        if protocol != "centrifuge":
            db += f"   capillary_number = {cap_num}\n"
        db += f"   F = {f_str}\n"
        db += f"   inletLayers = {inlet_layers_str}\n"
        db += f"   outletLayers = {outlet_layers_str}\n"
        db += "}\n\n"

        db += "FlowAdaptor {\n"
        if protocol == "fractional flow":
            db += f"   max_steady_timesteps = {fa_max}\n"
            db += f"   min_steady_timesteps = {fa_min}\n"
            db += f"   fractional_flow_increment = {fa_incr}\n"
            db += f"   mass_fraction_factor = {fa_mass}\n"
            db += f"   endpoint_threshold = {fa_ep}\n"
            db += f"   skip_timesteps = {fa_skip}\n"
            db += f"   fractional_flow_epsilon = {fa_ff_eps}\n"
        db += "}\n\n"

    elif model == "perm":
        db += "MRT {\n"
        db += f"   F = {f_str}\n"
        db += f"   tau = {perm_tau if perm_tau is not None else 0.7}\n"
        db += f"   tolerance = {perm_tolerance if perm_tolerance is not None else 1e-6}\n"
        db += f"   timestepMax = {perm_timestep_max if perm_timestep_max is not None else 10000000}\n"
        db += "}\n\n"

    db += "Analysis {\n"
    db += f'   restart_file = "{restart_filename}"\n'
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
    State(ids.DOMAIN_INLET_LAYERS, "value"),
    State(ids.DOMAIN_OUTLET_LAYERS, "value"),
    State(ids.DOMAIN_INLET_LAYERS_PHASE, "value"),
    State(ids.DOMAIN_OUTLET_LAYERS_PHASE, "value"),
    State(ids.COLOR_COMPONENT_AFFINITY, "value"),
    State(ids.FA_MAX_STEADY, "value"),
    State(ids.FA_MIN_STEADY, "value"),
    State(ids.FA_FF_INCREMENT, "value"),
    State(ids.FA_MASS_FRACTION, "value"),
    State(ids.FA_ENDPOINT_THRESH, "value"),
    State(ids.FA_SKIP_TIMESTEPS, "value"),
    State(ids.FA_FF_EPSILON, "value"),
    State("perm-tau", "value"),
    State("perm-tolerance", "value"),
    State("perm-timestep-max", "value"),
    State(ids.ANALYSIS_INTERVAL, "value"),
    State(ids.ANALYSIS_SUBPHASE_INTERVAL, "value"),
    State(ids.ANALYSIS_VIS_INTERVAL, "value"),
    State(ids.ANALYSIS_N_THREADS, "value"),
    State(ids.ANALYSIS_RESTART_INTERVAL, "value"),
    State(ids.ANALYSIS_RESTART_FILENAME, "value"),
    State(ids.VIS_SAVE_8BIT, "value"),
    State(ids.VIS_SAVE_PHASE, "value"),
    State(ids.VIS_SAVE_PRESSURE, "value"),
    State(ids.VIS_SAVE_VELOCITY, "value"),
    State(ids.MORPH_SW, "value"),
    prevent_initial_call=True,
)
def toggle_preview(_preview_clicks, _close_clicks, *args):
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
    State(ids.GEOMETRY_ARRAY_STORE, "data"),
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
    State(ids.DOMAIN_INLET_LAYERS, "value"),
    State(ids.DOMAIN_OUTLET_LAYERS, "value"),
    State(ids.DOMAIN_INLET_LAYERS_PHASE, "value"),
    State(ids.DOMAIN_OUTLET_LAYERS_PHASE, "value"),
    State(ids.COLOR_COMPONENT_AFFINITY, "value"),
    State(ids.FA_MAX_STEADY, "value"),
    State(ids.FA_MIN_STEADY, "value"),
    State(ids.FA_FF_INCREMENT, "value"),
    State(ids.FA_MASS_FRACTION, "value"),
    State(ids.FA_ENDPOINT_THRESH, "value"),
    State(ids.FA_FF_EPSILON, "value"),
    State(ids.FA_SKIP_TIMESTEPS, "value"),
    State("perm-tau", "value"),
    State("perm-tolerance", "value"),
    State("perm-timestep-max", "value"),
    State(ids.ANALYSIS_INTERVAL, "value"),
    State(ids.ANALYSIS_SUBPHASE_INTERVAL, "value"),
    State(ids.ANALYSIS_VIS_INTERVAL, "value"),
    State(ids.ANALYSIS_N_THREADS, "value"),
    State(ids.ANALYSIS_RESTART_INTERVAL, "value"),
    State(ids.ANALYSIS_RESTART_FILENAME, "value"),
    State(ids.VIS_SAVE_8BIT, "value"),
    State(ids.VIS_SAVE_PHASE, "value"),
    State(ids.VIS_SAVE_PRESSURE, "value"),
    State(ids.VIS_SAVE_VELOCITY, "value"),
    State(ids.MORPH_SW, "value"),
    prevent_initial_call=True,
)
def create_simulation_directory(
    _n_clicks, base_path, sim_name,
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
        if geo_source == "path" and geo_remote_path:
            from pathlib import Path as _Path
            geo_filename = _Path(geo_remote_path).name
            dst = posixpath.join(sim_dir, geo_filename)
            fs.put_file(geo_remote_path, dst)
            steps.append(dbc.ListGroupItem(f"✓ Copied geometry: {geo_filename}", color="success"))
        elif geo_store:
            import os
            import tempfile
            raw_bytes = base64.b64decode(geo_store["b64"])
            with tempfile.NamedTemporaryFile(delete=False, suffix=".raw") as tmp:
                tmp.write(raw_bytes)
                tmp_path = tmp.name
            geo_filename = sim_name + ".raw"
            dst = posixpath.join(sim_dir, geo_filename)
            fs.put_file(tmp_path, dst)
            os.unlink(tmp_path)
            steps.append(dbc.ListGroupItem(f"✓ Uploaded geometry: {geo_filename}", color="success"))
        elif geo_source == "dims":
            steps.append(dbc.ListGroupItem(
                "ℹ Geometry-free mode — no geometry file transferred.",
                color="info",
            ))
        else:
            steps.append(dbc.ListGroupItem(
                "⚠ No geometry file transferred — load a geometry file first.",
                color="warning",
            ))

    except Exception as e:
        steps.append(dbc.ListGroupItem(f"✗ Error: {e}", color="danger"))

    return dbc.ListGroup(steps)
