"""2D Slice Visualization page for the analysis dashboard.

Displays 2D slices of HDF5 output files or phase field (id_t*.raw) from LBPM simulations.
Allows slicing along any axis and stepping through timesteps.
"""

import re
import math
import numpy as np
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go

from pyLBPM.dashboard import ids, dataloader, script_export
from pyLBPM.filesystem import get_filesystem

dash.register_page(__name__, name="2D Slice Visualization", order=5)

sim_dir = dataloader.get_sim_dir()


def _tip(label_text, tip_id, tip_text=""):
    """Return a label + hoverable ⓘ icon with a tooltip (matching geometry page style)."""
    return html.Div(
        [
            dbc.Label(label_text, className="me-1 mb-0"),
            html.Span(
                "ⓘ",
                id=tip_id,
                style={
                    "cursor": "pointer",
                    "color": "#6c757d",
                    "fontSize": "0.85em",
                    "verticalAlign": "middle",
                },
            ),
            dbc.Tooltip(tip_text, target=tip_id, style={"white-space": "pre-wrap"}),
        ],
        className="d-flex align-items-center mb-1",
    )


def _fmt_ts(n):
    """Format timestep number with k/M suffixes to save space on slider."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".rstrip("0").rstrip(".")
    if n >= 1_000:
        return f"{n // 1000}k"
    return str(n)


layout = dbc.Container(
    fluid=True,
    style={"marginTop": "20px"},
    children=[
        dcc.Location(id="vis2d-location", refresh=False),
        dcc.Store(id=ids.VIS_2D_FILE_STORE),
        dcc.Interval(id=ids.VIS_2D_REFRESH_INTERVAL, interval=60_000, disabled=False),
        # Header row with title and Scan button
        dbc.Row(
            [
                dbc.Col([html.H1("2D Slice Visualization")], xs=9),
                dbc.Col(
                    [
                        dbc.Button(
                            "Scan for New Results",
                            id=ids.VIS_2D_DISCOVER_BTN,
                            color="success",
                            size="sm",
                            className="w-100",
                        ),
                    ],
                    xs=3,
                ),
            ],
            className="mb-2",
            align="center",
        ),
        html.Hr(),
        # Data selection controls + Render button
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label("Data key:"),
                        dcc.Dropdown(
                            id=ids.VIS_2D_DATA_KEY,
                            options=[],
                            value=None,
                        ),
                    ],
                    xs=3,
                ),
                dbc.Col(
                    [
                        dbc.Label("Slice axis:"),
                        dcc.Dropdown(
                            id=ids.VIS_2D_AXIS,
                            options=[
                                {"label": "X (yz-plane)", "value": 0},
                                {"label": "Y (xz-plane)", "value": 1},
                                {"label": "Z (xy-plane)", "value": 2},
                            ],
                            value=2,
                        ),
                    ],
                    xs=3,
                ),
                dbc.Col(
                    [
                        _tip(
                            "Downsample:",
                            ids.TOOLTIP_VIS_DOWNSAMPLE,
                            "Reduces data density by skipping every N voxels in each dimension.\n"
                            "Use higher values for faster rendering.",
                        ),
                        dcc.Dropdown(
                            id=ids.VIS_2D_DOWNSAMPLE,
                            options=[
                                {"label": "1 (No downsampling)", "value": 1},
                                {"label": "2", "value": 2},
                                {"label": "4", "value": 4},
                                {"label": "8", "value": 8},
                            ],
                            value=1,
                        ),
                    ],
                    xs=2,
                ),
                dbc.Col(
                    [
                        dbc.Button(
                            "Render",
                            id=ids.VIS_2D_RENDER_BTN,
                            color="primary",
                            className="w-100",
                        ),
                    ],
                    xs=2,
                ),
            ],
            className="mb-3",
            align="end",
        ),
        # Colorbar range controls
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label("Colorbar min:"),
                        dbc.Input(
                            id=ids.VIS_2D_CBAR_MIN,
                            type="number",
                            placeholder="auto",
                            debounce=True,
                        ),
                    ],
                    xs=3,
                ),
                dbc.Col(
                    [
                        dbc.Label("Colorbar max:"),
                        dbc.Input(
                            id=ids.VIS_2D_CBAR_MAX,
                            type="number",
                            placeholder="auto",
                            debounce=True,
                        ),
                    ],
                    xs=3,
                ),
                dbc.Col(
                    [
                        dbc.Button(
                            "Reset Range",
                            id=ids.VIS_2D_CBAR_RESET,
                            color="link",
                            size="sm",
                        ),
                    ],
                    xs=2,
                    className="d-flex align-items-end",
                ),
            ],
            className="mb-3",
        ),
        # Slice index slider (no marks)
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label("Slice index:"),
                        dcc.Slider(
                            id=ids.VIS_2D_SLICE_INDEX,
                            min=0,
                            max=0,
                            step=1,
                            value=0,
                            marks=None,
                            tooltip={"always_visible": False},
                        ),
                    ],
                    xs=12,
                ),
            ],
            className="mb-2",
        ),
        # Export button
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Button(
                            "Export Visualization Script",
                            id=ids.VIS_2D_EXPORT_BTN,
                            color="outline-primary",
                            size="sm",
                        ),
                    ],
                    xs=3,
                ),
            ],
            className="mb-2",
        ),
        # Plot area
        dcc.Loading(
            children=[
                dcc.Graph(id=ids.VIS_2D_GRAPH, style={"height": "600px"}),
            ],
            type="circle",
            color="#0d6efd",
        ),
        # Timestep slider (below plot)
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label("Timestep:"),
                        dcc.Slider(
                            id=ids.VIS_2D_TIMESTEP,
                            min=0,
                            max=0,
                            step=1,
                            value=0,
                            marks={},
                            tooltip={"always_visible": False},
                        ),
                    ],
                    xs=12,
                ),
            ],
            className="mt-3",
        ),
        # Download component and modal for export
        dcc.Download(id=ids.VIS_2D_DOWNLOAD),
        dbc.Modal(
            [
                dbc.ModalHeader("Export 2D Slice Script"),
                dbc.ModalBody(
                    [
                        dbc.Label("Backend:"),
                        dbc.RadioItems(
                            id=ids.VIS_2D_EXPORT_BACKEND,
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
                            id=ids.VIS_2D_EXPORT_FILENAME,
                            value="2d_slice.py",
                            type="text",
                        ),
                    ]
                ),
                dbc.ModalFooter(
                    [
                        dbc.Button(
                            "Save", id=ids.VIS_2D_EXPORT_CONFIRM, color="primary"
                        ),
                        dbc.Button(
                            "Cancel", id=ids.VIS_2D_EXPORT_CANCEL, color="secondary"
                        ),
                    ]
                ),
            ],
            id=ids.VIS_2D_EXPORT_MODAL,
        ),
    ],
)


@callback(
    Output(ids.VIS_2D_FILE_STORE, "data"),
    Input("vis2d-location", "pathname"),
    Input(ids.VIS_2D_REFRESH_INTERVAL, "n_intervals"),
    Input(ids.VIS_2D_DISCOVER_BTN, "n_clicks"),
    State(ids.APP_INPUT_FILE_PATH, "data"),
)
def discover_files(_pathname, _intervals, _discover, stored_filename):
    """Discover available VIS directories, raw files, and parse metadata."""
    try:
        # Glob for vis* directories and id_t*.raw files
        vis_dir_list = (
            list(sim_dir.glob("vis*"))
            + list(sim_dir.glob("VIS*"))
            + list(sim_dir.glob("Vis*"))
        )
        vis_dir_list = list(dict.fromkeys(vis_dir_list))

        id_t_files = list(sim_dir.glob("id_t*.raw")) + list(sim_dir.glob("ID_T*.raw"))
        id_t_files = list(dict.fromkeys(id_t_files))

        has_raw = len(id_t_files) > 0

        # Extract timesteps
        file_list = vis_dir_list if vis_dir_list else id_t_files
        file_names = [f.name for f in file_list]
        timesteps = [
            int(re.findall(r"\d+", name)[0])
            for name in file_names
            if re.findall(r"\d+", name)
        ]
        timesteps = sorted(set(timesteps))

        # Parse data keys and subdomains from HDF5
        data_keys = []
        has_h5 = any("vis" in name.lower() for name in file_names)

        if has_h5:
            try:
                vis_xmf = list(sim_dir.glob("vis*/summary.xmf")) + list(
                    sim_dir.glob("VIS*/summary.xmf")
                )
                if vis_xmf:
                    data_keys = dataloader._get_data_keys(vis_xmf[0])
            except (IndexError, FileNotFoundError, Exception):
                pass

        if has_raw:
            data_keys.append("phase configurations")

        # Auto-compute downsample default based on domain size
        default_downsample = 1
        try:
            input_filename = stored_filename or "input.db"
            if (sim_dir / input_filename).exists():
                nx, ny, nz = dataloader.get_domain_dims(
                    sim_dir, input_filename=input_filename
                )
                domain_voxels = nx * ny * nz
                if domain_voxels > 100_000:
                    default_downsample = max(
                        1, math.ceil((domain_voxels / 100_000) ** (1 / 3))
                    )
        except Exception:
            pass

        return {
            "timesteps": timesteps,
            "data_keys": data_keys,
            "has_raw": has_raw,
            "default_downsample": default_downsample,
        }
    except Exception as e:
        return {
            "timesteps": [],
            "data_keys": [],
            "has_raw": False,
            "default_downsample": 1,
        }


@callback(
    Output(ids.VIS_2D_DATA_KEY, "options"),
    Output(ids.VIS_2D_DATA_KEY, "value"),
    Output(ids.VIS_2D_TIMESTEP, "max"),
    Output(ids.VIS_2D_TIMESTEP, "marks"),
    Output(ids.VIS_2D_DOWNSAMPLE, "value"),
    Input(ids.VIS_2D_FILE_STORE, "data"),
    State(ids.VIS_2D_DATA_KEY, "value"),
    State(ids.VIS_2D_TIMESTEP, "value"),
    State(ids.VIS_2D_DOWNSAMPLE, "value"),
)
def populate_controls(
    file_store_data, current_data_key, current_timestep, current_downsample
):
    """Populate control options and preserve session state."""
    if not file_store_data:
        return [], None, 0, {}, 1

    timesteps = file_store_data.get("timesteps", [])
    data_keys = file_store_data.get("data_keys", [])
    default_downsample = file_store_data.get("default_downsample", 1)

    # Data key options and value
    data_key_opts = [{"label": k, "value": k} for k in data_keys]
    data_key_val = (
        current_data_key
        if current_data_key in data_keys
        else (data_keys[0] if data_keys else None)
    )

    # Timestep slider
    max_timestep = len(timesteps) - 1 if timesteps else 0
    timestep_val = min(current_timestep or 0, max_timestep)
    step_size = max(1, len(timesteps) // 10) if timesteps else 1
    marks = {
        i: _fmt_ts(timesteps[i]) if i < len(timesteps) else ""
        for i in range(0, len(timesteps), step_size)
    }
    if max_timestep not in marks and max_timestep >= 0:
        marks[max_timestep] = (
            _fmt_ts(timesteps[max_timestep]) if max_timestep < len(timesteps) else ""
        )

    # Downsample: use default on first load, preserve on refresh
    downsample_val = current_downsample if current_downsample else default_downsample

    return data_key_opts, data_key_val, max_timestep, marks, downsample_val


@callback(
    Output(ids.VIS_2D_SLICE_INDEX, "max"),
    Input(ids.VIS_2D_FILE_STORE, "data"),
    Input(ids.VIS_2D_AXIS, "value"),
    Input(ids.VIS_2D_DOWNSAMPLE, "value"),
    State(ids.APP_INPUT_FILE_PATH, "data"),
)
def update_slice_max(file_store_data, axis, downsample, stored_filename):
    """Update slice index max based on chosen axis and downsample factor."""
    if not file_store_data or axis is None:
        return 0

    try:
        input_filename = stored_filename or "input.db"
        if (sim_dir / input_filename).exists():
            nx, ny, nz = dataloader.get_domain_dims(
                sim_dir, input_filename=input_filename
            )
            dims = [nx, ny, nz]
            max_idx = (dims[axis] // (downsample or 1)) - 1
            return max(0, max_idx)
    except Exception:
        pass

    return 0


@callback(
    Output(ids.VIS_2D_GRAPH, "figure"),
    Input(ids.VIS_2D_SLICE_INDEX, "value"),
    Input(ids.VIS_2D_TIMESTEP, "value"),
    Input(ids.VIS_2D_RENDER_BTN, "n_clicks"),
    State(ids.VIS_2D_DATA_KEY, "value"),
    State(ids.VIS_2D_AXIS, "value"),
    State(ids.VIS_2D_DOWNSAMPLE, "value"),
    State(ids.VIS_2D_CBAR_MIN, "value"),
    State(ids.VIS_2D_CBAR_MAX, "value"),
    State(ids.VIS_2D_FILE_STORE, "data"),
    State(ids.APP_INPUT_FILE_PATH, "data"),
    prevent_initial_call=True,
)
def render_plot(
    slice_idx,
    slider_step,
    render_clicks,
    data_key,
    axis,
    downsample,
    cbar_min,
    cbar_max,
    file_store_data,
    stored_filename,
):
    """Render the 2D slice visualization based on current selections."""
    if not file_store_data or data_key is None or axis is None or slice_idx is None:
        return go.Figure().add_annotation(text="Select data and axis")

    input_filename = stored_filename or "input.db"
    timesteps = file_store_data.get("timesteps", [])
    has_raw = file_store_data.get("has_raw", False)

    if not timesteps or slider_step is None or slider_step >= len(timesteps):
        return go.Figure().add_annotation(text="No valid timestep selected")

    sim_step = timesteps[slider_step]

    try:
        # Handle phase configurations (raw files)
        if data_key == "phase configurations":
            if not has_raw:
                return go.Figure().add_annotation(text="No raw phase files found")

            try:
                if not (sim_dir / input_filename).exists():
                    return go.Figure().add_annotation(
                        text=f"Error: {input_filename} not found"
                    )

                nx, ny, nz = dataloader.get_domain_dims(
                    sim_dir, input_filename=input_filename
                )

                img = dataloader.raw_reader(
                    simulation_dir=sim_dir,
                    raw_file=f"id_t{sim_step}.raw",
                    img_shape=(nx, ny, nz),
                    data_type=np.uint8,
                )

                # Apply downsample
                img = img[::downsample, ::downsample, ::downsample]

                # Take 2D slice
                if axis == 0:
                    slice_arr = img[slice_idx, :, :]
                elif axis == 1:
                    slice_arr = img[:, slice_idx, :]
                else:  # axis == 2
                    slice_arr = img[:, :, slice_idx]

                fig = px.imshow(
                    slice_arr,
                    color_continuous_scale="RdBu",
                    aspect="equal",
                    title=f"Phase Configuration (id_t{sim_step}) - Slice {slice_idx} along Axis {axis}",
                    zmin=cbar_min if cbar_min is not None else None,
                    zmax=cbar_max if cbar_max is not None else None,
                )
                fig.update_layout(height=600, xaxis_title="", yaxis_title="")
                return fig

            except Exception as e:
                return go.Figure().add_annotation(
                    text=f"Error loading phase configurations: {str(e)}"
                )

        # HDF5 path
        else:
            try:
                img = dataloader.h5_reader(
                    simulation_dir=sim_dir / f"vis{sim_step}",
                    data_key=data_key,
                    subdomain_num=["all"],
                    input_db_path=sim_dir,
                    input_filename=input_filename,
                )

                # Apply downsample
                img = img[::downsample, ::downsample, ::downsample]

                # Take 2D slice
                if axis == 0:
                    slice_arr = img[slice_idx, :, :]
                elif axis == 1:
                    slice_arr = img[:, slice_idx, :]
                else:  # axis == 2
                    slice_arr = img[:, :, slice_idx]

                fig = px.imshow(
                    slice_arr,
                    color_continuous_scale="Turbo",
                    aspect="equal",
                    title=f"{data_key} (vis{sim_step}) - Slice {slice_idx} along Axis {axis}",
                    zmin=cbar_min if cbar_min is not None else None,
                    zmax=cbar_max if cbar_max is not None else None,
                )
                fig.update_layout(height=600, xaxis_title="", yaxis_title="")
                return fig

            except Exception as e:
                return go.Figure().add_annotation(
                    text=f"Error loading HDF5 data: {str(e)}"
                )

    except Exception as e:
        return go.Figure().add_annotation(
            text=f"Error rendering visualization: {str(e)}"
        )


@callback(
    Output(ids.VIS_2D_CBAR_MIN, "value"),
    Output(ids.VIS_2D_CBAR_MAX, "value"),
    Input(ids.VIS_2D_DATA_KEY, "value"),
    Input(ids.VIS_2D_CBAR_RESET, "n_clicks"),
    prevent_initial_call=True,
)
def reset_colorbar_range(_data_key, _reset):
    """Reset colorbar range when data key changes or reset button is clicked."""
    return None, None


@callback(
    Output(ids.VIS_2D_EXPORT_MODAL, "is_open"),
    Input(ids.VIS_2D_EXPORT_BTN, "n_clicks"),
    Input(ids.VIS_2D_EXPORT_CONFIRM, "n_clicks"),
    Input(ids.VIS_2D_EXPORT_CANCEL, "n_clicks"),
    State(ids.VIS_2D_EXPORT_MODAL, "is_open"),
    prevent_initial_call=True,
)
def toggle_export_modal(export_clicks, confirm_clicks, cancel_clicks, is_open):
    """Toggle export modal visibility."""
    if export_clicks or cancel_clicks:
        return not is_open
    return is_open


@callback(
    Output(ids.VIS_2D_DOWNLOAD, "data"),
    Input(ids.VIS_2D_EXPORT_CONFIRM, "n_clicks"),
    State(ids.VIS_2D_DATA_KEY, "value"),
    State(ids.VIS_2D_AXIS, "value"),
    State(ids.VIS_2D_SLICE_INDEX, "value"),
    State(ids.VIS_2D_TIMESTEP, "value"),
    State(ids.VIS_2D_DOWNSAMPLE, "value"),
    State(ids.VIS_2D_FILE_STORE, "data"),
    State(ids.APP_INPUT_FILE_PATH, "data"),
    State(ids.VIS_2D_EXPORT_FILENAME, "value"),
    State(ids.VIS_2D_EXPORT_BACKEND, "value"),
    prevent_initial_call=True,
)
def generate_script(
    n_clicks,
    data_key,
    axis,
    slice_idx,
    slider_step,
    downsample,
    file_store_data,
    stored_filename,
    filename,
    backend,
):
    """Generate and download the 2D visualization script."""
    if (
        not n_clicks
        or not data_key
        or axis is None
        or slice_idx is None
        or not filename
    ):
        return None

    input_filename = stored_filename or "input.db"
    timesteps = file_store_data.get("timesteps", []) if file_store_data else []

    if not timesteps or slider_step is None or slider_step >= len(timesteps):
        return None

    timestep = timesteps[slider_step]

    if backend == "matplotlib":
        script_content = script_export.vis_2d_script_matplotlib(
            str(sim_dir),
            data_key,
            timestep,
            axis,
            slice_idx,
            downsample or 1,
            input_filename,
        )
    else:
        script_content = script_export.vis_2d_script(
            str(sim_dir),
            data_key,
            timestep,
            axis,
            slice_idx,
            downsample or 1,
            input_filename,
        )

    return dict(content=script_content, filename=filename)
