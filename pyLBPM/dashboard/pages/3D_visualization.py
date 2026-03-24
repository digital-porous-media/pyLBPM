"""3D Visualization page for the analysis dashboard.

Displays VTK visualization of HDF5 output files from LBPM simulations.
Can use either vis*/summary.xmf files or id_t*.raw files.
"""

import re
import math
import numpy as np
import diskcache
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output, State
import plotly.express as px

from pyLBPM.dashboard import ids, dataloader, plotter, script_export
from pyLBPM.filesystem import get_filesystem

dash.register_page(__name__, name="3D Visualization", order=6)

# Initialize disk cache for array caching
cache = diskcache.Cache("./.dash_cache/vis3d")


def _tip(label_text, tip_id, tip_text=""):
    """Return a label + hoverable ⓘ icon with a tooltip (matching geometry page style)."""
    return html.Div([
        dbc.Label(label_text, className="me-1 mb-0"),
        html.Span("ⓘ", id=tip_id,
                  style={"cursor": "pointer", "color": "#6c757d",
                         "fontSize": "0.85em", "verticalAlign": "middle"}),
        dbc.Tooltip(tip_text, target=tip_id, style={"white-space": "pre-wrap"}),
    ], className="d-flex align-items-center mb-1")


def _fmt_ts(n):
    """Format timestep number with k/M suffixes to save space on slider."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".rstrip("0").rstrip(".")
    if n >= 1_000:
        return f"{n // 1000}k"
    return str(n)

sim_dir = dataloader.get_sim_dir()

layout = dbc.Container(
    fluid=True,
    style={"marginTop": "20px"},
    children=[
        dcc.Location(id="vis3d-location", refresh=False),
        dcc.Store(id=ids.VIS_3D_FILE_STORE),
        dcc.Store(id=ids.VIS_3D_RENDER_PARAMS_STORE, storage_type="session"),
        dcc.Interval(id=ids.VIS_3D_REFRESH_INTERVAL, interval=60_000, disabled=True),

        # Header row with title and Scan button
        dbc.Row([
            dbc.Col([html.H1("3D Visualization")], xs=9),
            dbc.Col([
                dbc.Button("Scan for New Results", id=ids.VIS_3D_DISCOVER_BTN, color="success",
                           size="sm", className="w-100"),
            ], xs=3),
        ], className="mb-2", align="center"),
        html.Hr(),

        # Data selection controls (dropdowns) + Render button
        dbc.Row([
            dbc.Col([
                dbc.Label("Data key:"),
                dcc.Dropdown(
                    id=ids.VIS_3D_DATA_KEY,
                    options=[],
                    value=None,
                ),
            ], xs=3),
            dbc.Col([
                dbc.Label("Subdomains:"),
                dcc.Dropdown(
                    id=ids.VIS_3D_SUBDOMAIN,
                    options=[],
                    value=["all"],
                    multi=True,
                ),
            ], xs=3),
            dbc.Col([
                _tip("Downsample:", ids.TOOLTIP_VIS_DOWNSAMPLE,
                     "Reduces data density by skipping every N voxels in each dimension.\n"
                     "Factor of 2 = 1/8 of the data, factor of 4 = 1/64 of the data.\n"
                     "Use higher values for faster rendering of large datasets."),
                dcc.Dropdown(
                    id=ids.VIS_3D_DOWNSAMPLE,
                    options=[
                        {"label": "1 (No downsampling)", "value": 1},
                        {"label": "2", "value": 2},
                        {"label": "4", "value": 4},
                        {"label": "8", "value": 8},
                    ],
                    value=1,
                ),
            ], xs=3),
            dbc.Col([
                dbc.Button(
                    "Render",
                    id=ids.VIS_3D_RENDER_BTN,
                    color="primary",
                    className="w-100",
                ),
            ], xs=2),
        ], className="mb-2", align="end"),

        # Export button on its own row
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    "Export Visualization Script",
                    id=ids.VIS_3D_EXPORT_BTN,
                    color="outline-primary",
                    size="sm",
                ),
            ], xs=3),
        ], className="mb-3"),

        # Timestep slider
        dbc.Row([
            dbc.Col([
                dbc.Label("Timestep:"),
                dcc.Slider(
                    id=ids.VIS_3D_TIMESTEP,
                    min=0,
                    max=0,
                    step=1,
                    value=0,
                    marks={},
                    tooltip={"always_visible": False},
                ),
            ], xs=12),
        ], className="mb-3"),

        # VTK rendering area (key forces remount to clear broken JS state)
        dcc.Loading(
            children=[
                html.Div(
                    id=ids.VTK_3D_VIS,
                    style={"width": "100%", "height": "600px"},
                    key="vtk-container",
                ),
            ],
            type="circle",
            color="#0d6efd",
        ),

        # Download component and modal for export
        dcc.Download(id=ids.VIS_3D_DOWNLOAD),
        dbc.Modal([
            dbc.ModalHeader("Export 3D Visualization Script"),
            dbc.ModalBody([
                dbc.Label("Filename:"),
                dbc.Input(id=ids.VIS_3D_EXPORT_FILENAME, value="3d_visualization.py", type="text"),
            ]),
            dbc.ModalFooter([
                dbc.Button("Save", id=ids.VIS_3D_EXPORT_CONFIRM, color="primary"),
                dbc.Button("Cancel", id=ids.VIS_3D_EXPORT_CANCEL, color="secondary"),
            ]),
        ], id=ids.VIS_3D_EXPORT_MODAL),
    ],
)


@callback(
    Output(ids.VIS_3D_FILE_STORE, "data"),
    Input("vis3d-location", "pathname"),
    Input(ids.VIS_3D_REFRESH_INTERVAL, "n_intervals"),
    Input(ids.VIS_3D_DISCOVER_BTN, "n_clicks"),
    State(ids.APP_INPUT_FILE_PATH, "data"),
)
def discover_files(_pathname, _intervals, _discover, stored_filename):
    """Discover available VIS directories, raw files, and parse metadata."""
    try:
        # Glob for vis* directories and id_t*.raw files
        vis_dir_list = list(sim_dir.glob("vis*")) + list(sim_dir.glob("VIS*")) + list(sim_dir.glob("Vis*"))
        vis_dir_list = list(dict.fromkeys(vis_dir_list))  # deduplicate

        id_t_files = list(sim_dir.glob("id_t*.raw")) + list(sim_dir.glob("ID_T*.raw"))
        id_t_files = list(dict.fromkeys(id_t_files))

        has_raw = len(id_t_files) > 0

        # Extract timesteps
        file_list = vis_dir_list if vis_dir_list else id_t_files
        file_names = [f.name for f in file_list]
        timesteps = [int(re.findall(r"\d+", name)[0]) for name in file_names if re.findall(r"\d+", name)]
        timesteps = sorted(set(timesteps))

        # Parse data keys and subdomains from HDF5
        data_keys = []
        grid_names = []
        has_h5 = any("vis" in name.lower() for name in file_names)

        if has_h5:
            try:
                vis_xmf = list(sim_dir.glob("vis*/summary.xmf")) + list(sim_dir.glob("VIS*/summary.xmf"))
                if vis_xmf:
                    data_keys = dataloader._get_data_keys(vis_xmf[0])
                    grid_names, _ = dataloader._get_grid_names(vis_xmf[0])
            except (IndexError, FileNotFoundError, Exception):
                pass

        if has_raw:
            data_keys.append("phase configurations")

        grid_names.append("all")

        # Auto-compute downsample default based on domain size
        default_downsample = 1
        try:
            input_filename = stored_filename or "input.db"
            if (sim_dir / input_filename).exists():
                nx, ny, nz = dataloader.get_domain_dims(sim_dir, input_filename=input_filename)
                domain_voxels = nx * ny * nz
                if domain_voxels > 100_000:
                    default_downsample = max(1, math.ceil((domain_voxels / 100_000) ** (1/3)))
        except Exception:
            pass

        return {
            "timesteps": timesteps,
            "data_keys": data_keys,
            "subdomains": grid_names,
            "has_raw": has_raw,
            "default_downsample": default_downsample,
        }
    except Exception as e:
        return {
            "timesteps": [],
            "data_keys": [],
            "subdomains": [],
            "has_raw": False,
            "default_downsample": 1,
        }


@callback(
    Output(ids.VIS_3D_DATA_KEY, "options"),
    Output(ids.VIS_3D_DATA_KEY, "value"),
    Output(ids.VIS_3D_SUBDOMAIN, "options"),
    Output(ids.VIS_3D_SUBDOMAIN, "value"),
    Output(ids.VIS_3D_TIMESTEP, "max"),
    Output(ids.VIS_3D_TIMESTEP, "marks"),
    Output(ids.VIS_3D_DOWNSAMPLE, "value"),
    Input(ids.VIS_3D_FILE_STORE, "data"),
    State(ids.VIS_3D_DATA_KEY, "value"),
    State(ids.VIS_3D_SUBDOMAIN, "value"),
    State(ids.VIS_3D_TIMESTEP, "value"),
    State(ids.VIS_3D_DOWNSAMPLE, "value"),
)
def populate_controls(file_store_data, current_data_key, current_subdomains, current_timestep, current_downsample):
    """Populate control options and preserve session state."""
    if not file_store_data:
        return [], None, [], ["all"], 0, {}, 1

    timesteps = file_store_data.get("timesteps", [])
    data_keys = file_store_data.get("data_keys", [])
    subdomains = file_store_data.get("subdomains", [])
    default_downsample = file_store_data.get("default_downsample", 1)

    # Data key options and value
    data_key_opts = [{"label": k, "value": k} for k in data_keys]
    data_key_val = current_data_key if current_data_key in data_keys else (data_keys[0] if data_keys else None)

    # Subdomain options and value
    subdomain_opts = [{"label": s, "value": s} for s in subdomains]
    # Filter current subdomains to only include those still in the list
    valid_subdomains = [s for s in (current_subdomains or []) if s in subdomains]
    subdomain_val = valid_subdomains if valid_subdomains else ["all"]

    # Timestep slider
    max_timestep = len(timesteps) - 1 if timesteps else 0
    # Preserve slider position unless it's out of range
    timestep_val = min(current_timestep or 0, max_timestep)
    # Create marks for every 10th timestep or fewer
    step_size = max(1, len(timesteps) // 10) if timesteps else 1
    marks = {i: _fmt_ts(timesteps[i]) if i < len(timesteps) else "" for i in range(0, len(timesteps), step_size)}
    if max_timestep not in marks and max_timestep >= 0:
        marks[max_timestep] = _fmt_ts(timesteps[max_timestep]) if max_timestep < len(timesteps) else ""

    # Downsample: use default on first load, preserve on refresh
    downsample_val = current_downsample if current_downsample else default_downsample

    return data_key_opts, data_key_val, subdomain_opts, subdomain_val, max_timestep, marks, downsample_val


@callback(
    Output(ids.VIS_3D_SUBDOMAIN, "disabled"),
    Input(ids.VIS_3D_DATA_KEY, "value"),
)
def disable_subdomain_for_phase(data_key):
    """Disable subdomain selection when phase configurations is selected."""
    return data_key == "phase configurations"


@callback(
    Output(ids.VIS_3D_SUBDOMAIN, "value", allow_duplicate=True),
    Output(ids.VIS_3D_SUBDOMAIN, "options", allow_duplicate=True),
    Input(ids.VIS_3D_SUBDOMAIN, "value"),
    State(ids.VIS_3D_FILE_STORE, "data"),
    prevent_initial_call=True,
)
def enforce_all_exclusive(selected_values, file_store_data):
    """Enforce mutual exclusivity for 'all' subdomain selection."""
    if not file_store_data:
        raise dash.exceptions.PreventUpdate

    subdomains = file_store_data.get("subdomains", [])
    all_options = [{"label": s, "value": s} for s in subdomains]

    if selected_values and "all" in selected_values:
        # Force value to only ["all"] and disable all non-"all" options
        new_value = ["all"]
        new_options = [
            {**opt, "disabled": opt["value"] != "all"}
            for opt in all_options
        ]
    else:
        # Allow any selection (including empty), ensure all options are enabled
        new_value = selected_values or []
        new_options = [{**opt, "disabled": False} for opt in all_options]

    return new_value, new_options


@callback(
    Output(ids.VTK_3D_VIS, "children"),
    Output(ids.VIS_3D_RENDER_PARAMS_STORE, "data"),
    Input(ids.VIS_3D_RENDER_BTN, "n_clicks"),
    Input("vis3d-location", "pathname"),
    State(ids.VIS_3D_DATA_KEY, "value"),
    State(ids.VIS_3D_SUBDOMAIN, "value"),
    State(ids.VIS_3D_TIMESTEP, "value"),
    State(ids.VIS_3D_DOWNSAMPLE, "value"),
    State(ids.VIS_3D_FILE_STORE, "data"),
    State(ids.APP_INPUT_FILE_PATH, "data"),
    State(ids.VIS_3D_RENDER_PARAMS_STORE, "data"),
    prevent_initial_call=True,
)
def render_vis(n_clicks, _pathname, data_key, subdomains, slider_step, downsample,
               file_store_data, stored_filename, render_params):
    """Render the 3D visualization based on current selections."""
    triggered = dash.ctx.triggered_id

    if triggered == "vis3d-location":
        # Re-render using saved params from previous session if available
        if not render_params:
            raise dash.exceptions.PreventUpdate
        data_key = render_params.get("data_key", data_key)
        subdomains = render_params.get("subdomains", subdomains)
        slider_step = render_params.get("slider_step", slider_step)
        downsample = render_params.get("downsample", downsample)
        file_store_data = render_params.get("file_store_data", file_store_data)
        stored_filename = render_params.get("stored_filename", stored_filename)
        params_update = dash.no_update
    else:
        # Button click — save params so page-return can re-render
        if not file_store_data or n_clicks is None:
            return html.Div("Click Render to display visualization"), dash.no_update
        params_update = {
            "data_key": data_key,
            "subdomains": subdomains,
            "slider_step": slider_step,
            "downsample": downsample,
            "file_store_data": file_store_data,
            "stored_filename": stored_filename,
        }

    input_filename = stored_filename or "input.db"
    timesteps = file_store_data.get("timesteps", []) if file_store_data else []
    has_raw = file_store_data.get("has_raw", False) if file_store_data else False

    if not timesteps or slider_step is None or slider_step >= len(timesteps):
        return html.Div("No valid timestep selected"), dash.no_update

    sim_step = timesteps[slider_step]

    try:
        # Handle "phase configurations" (raw files)
        if data_key == "phase configurations":
            if not has_raw:
                return html.Div("No raw phase files found"), dash.no_update

            try:
                if not (sim_dir / input_filename).exists():
                    return html.Div(f"Error: {input_filename} not found. Cannot determine domain dimensions for raw files."), dash.no_update

                nx, ny, nz = dataloader.get_domain_dims(sim_dir, input_filename=input_filename)

                # Check cache
                cache_key = (str(sim_dir), sim_step, "phase_raw", data_key)
                if cache_key in cache:
                    img = cache[cache_key]
                else:
                    img = dataloader.raw_reader(
                        simulation_dir=sim_dir,
                        raw_file=f"id_t{sim_step}.raw",
                        img_shape=(nx, ny, nz),
                        data_type=np.uint8
                    )
                    cache[cache_key] = img

                # Apply downsample
                img = img[::downsample, ::downsample, ::downsample]

                view = plotter.render_phase_isosurfaces(img)

                return html.Div(
                    key=f"vtk-phase-{sim_step}-{downsample}",
                    style={"width": "100%", "height": "600px"},
                    children=[view],
                ), params_update
            except Exception as e:
                return html.Div(f"Error loading phase configurations: {str(e)}"), dash.no_update

        # HDF5 path
        else:
            try:
                # Check cache
                subdomain_key = frozenset(subdomains) if isinstance(subdomains, list) else subdomains
                cache_key = (str(sim_dir), sim_step, subdomain_key, data_key)

                if cache_key in cache:
                    img = cache[cache_key]
                else:
                    img = dataloader.h5_reader(
                        simulation_dir=sim_dir / f"vis{sim_step}",
                        data_key=data_key,
                        subdomain_num=subdomains,
                        input_db_path=sim_dir,
                        input_filename=input_filename,
                    )
                    cache[cache_key] = img

                # Apply downsample
                img = img[::downsample, ::downsample, ::downsample]

                view = plotter.render_volume(img)

                return html.Div(
                    key=f"vtk-h5-{data_key}-{sim_step}-{downsample}",
                    style={"width": "100%", "height": "600px"},
                    children=[view],
                ), params_update
            except Exception as e:
                return html.Div(f"Error loading HDF5 data: {str(e)}"), dash.no_update

    except Exception as e:
        return html.Div(f"Error rendering visualization: {str(e)}"), dash.no_update


@callback(
    Output(ids.VIS_3D_EXPORT_MODAL, "is_open"),
    Input(ids.VIS_3D_EXPORT_BTN, "n_clicks"),
    Input(ids.VIS_3D_EXPORT_CONFIRM, "n_clicks"),
    Input(ids.VIS_3D_EXPORT_CANCEL, "n_clicks"),
    State(ids.VIS_3D_EXPORT_MODAL, "is_open"),
    prevent_initial_call=True,
)
def toggle_export_modal(export_clicks, confirm_clicks, cancel_clicks, is_open):
    """Toggle export modal visibility."""
    if export_clicks or cancel_clicks:
        return not is_open
    return is_open


@callback(
    Output(ids.VIS_3D_DOWNLOAD, "data"),
    Input(ids.VIS_3D_EXPORT_CONFIRM, "n_clicks"),
    State(ids.VIS_3D_DATA_KEY, "value"),
    State(ids.VIS_3D_TIMESTEP, "value"),
    State(ids.VIS_3D_SUBDOMAIN, "value"),
    State(ids.VIS_3D_DOWNSAMPLE, "value"),
    State(ids.VIS_3D_FILE_STORE, "data"),
    State(ids.APP_INPUT_FILE_PATH, "data"),
    State(ids.VIS_3D_EXPORT_FILENAME, "value"),
    prevent_initial_call=True,
)
def generate_script(n_clicks, data_key, slider_step, subdomains, downsample, file_store_data,
                    stored_filename, filename):
    """Generate and download the 3D visualization script."""
    if not n_clicks or not data_key or not filename:
        return None

    input_filename = stored_filename or "input.db"
    timesteps = file_store_data.get("timesteps", []) if file_store_data else []

    if not timesteps or slider_step is None or slider_step >= len(timesteps):
        return None

    timestep = timesteps[slider_step]
    subdomain_list = subdomains if isinstance(subdomains, list) else [subdomains]

    script_content = script_export.vis_3d_script(str(sim_dir), data_key, timestep, subdomain_list,
                                                 downsample or 1, input_filename)

    return dict(content=script_content, filename=filename)
