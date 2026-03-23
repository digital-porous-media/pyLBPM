# pyLBPM — Developer Guide

## Project Purpose

pyLBPM is a Python interface for **LBPM** (Lattice Boltzmann Pore-scale Modeling), a C++/CUDA
simulator for fluid dynamics in porous media, typically run on HPC clusters (TACC, etc.). This
package provides:

1. Python classes for configuring LBPM simulations (`domain_db`, `color_db`, `permeability_db`, etc.)
2. A **pre-simulation setup dashboard** for configuring, validating, and launching simulations
3. A **simulation/post-simulation analysis dashboard** for monitoring jobs and visualizing results

---

## Two-Dashboard Architecture

| Dashboard | Entry Point | Purpose |
|-----------|-------------|---------|
| **Setup** | `pyLBPM/lbpm_setup_dashboard.py` | Configure geometry, edit input params, create sim directory on HPC |
| **Analysis** | `pyLBPM/lbpm_dashboard.py` | Monitor running jobs, analyze results in real-time |

Run the setup dashboard:
```bash
python -m pyLBPM.lbpm_setup_dashboard
```

Run the analysis dashboard:
```bash
python -m pyLBPM.lbpm_dashboard --sim-dir /path/to/simulation
```

> **Note**: The LBPM binary (`lbpm_color_simulator`, etc.) can only be installed on Linux.
> The dashboards themselves run on any OS.

---

## Stack

| Component | Library |
|-----------|---------|
| Web framework | [Dash](https://dash.plotly.com/) + [dash-bootstrap-components](https://dash-bootstrap-components.opensource.faculty.ai/) |
| Charts | Plotly Express |
| 3D visualization | dash-vtk, pyvista |
| HDF5 / raw data I/O | h5py, numpy |
| HPC connectivity | paramiko (SFTP), tapipy (Tapis v3), globus-sdk (Globus) |
| Config parsing | PyYAML, custom `.db` parser (`lbpm_input_database.py`) |

---

## Development Environment

### Setup

This project uses a conda environment for dependency management. To activate the environment:

```bash
conda activate pylbpm
```

If the environment doesn't exist, create it from the environment file (if present) or install dependencies manually:

```bash
conda create -n pylbpm python=3.10
conda activate pylbpm
pip install -r requirements.txt
```

### Running Tests and Code

When running Python code (including tests, scripts, and the Claude Code integration), **always activate the pylbpm conda environment first**:

```bash
# Run tests
conda activate pylbpm
pytest tests/

# Run the analysis dashboard
conda activate pylbpm
python -m pyLBPM.lbpm_dashboard --sim-dir /path/to/simulation

# Run the setup dashboard
conda activate pylbpm
python -m pyLBPM.lbpm_setup_dashboard
```

---

## File Format Conventions

| Extension | Format | Usage |
|-----------|--------|-------|
| `.db` | Plain text, block sections (`Domain { ... }`) | LBPM simulation input |
| `.raw` | Flat binary uint8 (C-order, z fastest) | 3D geometry and phase field images |
| `.csv` | Space-delimited | timelog, SCAL, subphase, morphdrain output |
| `.h5` / `.xmf` | HDF5 + XML metadata | Pressure, velocity, phase field (parallel output) |

### LBPM Label Convention (important)
In `.raw` geometry files, integer voxel labels map to LBPM phases as follows:
- Values **≤ 0** → solid / immobile phase (`ComponentLabels`)
- Value **1** → non-wetting fluid (NWP, e.g. oil)
- Value **2** → wetting fluid (WP, e.g. water)

`ReadValues` in `input.db` lists the original image labels; `WriteValues` remaps them to LBPM
convention. By default `WriteValues = ReadValues` but users must edit to match LBPM convention.

### Axis Convention
Geometry files are stored in **C-order** (row-major): `array[x, y, z]` where `z` is the
fastest-varying index in memory. LBPM reads the file the same way. The body force `F = [Fx, Fy, Fz]`
aligns with array dimensions 0, 1, 2 respectively.

---

## Dashboard Page Structure

### Setup Dashboard (`lbpm_setup_dashboard.py`)
Pages are in `pyLBPM/dashboard/setup_pages/`:

| Order | Page | File | Description |
|-------|------|------|-------------|
| 0 | Geometry Setup | `geometry_setup.py` | Load geometry, set dimensions, flow direction, domain/model params, create sim dir |
| 1 | Input Configuration | `input_config_preview.py` | Syntax-highlighted view + manual edit of `input.db` |

### Analysis Dashboard (`lbpm_dashboard.py`)
Pages are in `pyLBPM/dashboard/pages/`:

| Order | Page | File | Required Files |
|-------|------|------|----------------|
| 0 | Input Configuration | `input_file.py` | `input.db` |
| 1 | Pre-Simulation | `presimulation.py` | `morphdrain.csv`, `*.morphdrain.raw` |
| 2 | Monitor | `monitor.py` | `timelog.csv` |
| 3 | Subphase Analysis | `subphase_analysis.py` | `subphase.csv` |
| 4 | SCAL Analysis | `SCAL.py` | `SCAL.csv` |
| 5 | 3D Visualization | `3D_visualization.py` | `vis*/summary.xmf`, `*.h5` |

---

## HPC Filesystem Abstraction

All file I/O uses a backend-agnostic `HPCFilesystem` interface (`pyLBPM/filesystem/`).

**Current implementation**: Simplified to **local filesystem only** (wraps `pathlib.Path`).

All page modules use `get_filesystem()` to read data:
```python
from pyLBPM.filesystem import get_filesystem

fs = get_filesystem()
csv_bytes = fs.read_file(csv_path)
```

This abstraction makes it straightforward to add remote backends (SFTP, Tapis, Globus) in the future without changing page code.

---

## Key Python Classes

| Class | File | Purpose |
|-------|------|---------|
| `domain_db` | `lbpm_domain.py` | Manages 3D simulation domain; generates `Domain {}` config block |
| `color_db` | `lbpm_color_model.py` | Two-phase (Color LBM) config; includes `FlowAdaptor_db`, `Analysis_db`, `Visualization_db` |
| `permeability_db` | `lbpm_permeability_model.py` | Single-phase (MRT) permeability config |
| `morph_db` | `lbpm_morphology.py` | Morphological pre-analysis (drainage/opening) |
| `HPCFilesystem` | `filesystem/base.py` | Abstract base for all HPC filesystem backends |

### `color_db` default parameters
```python
tauA = tauB = 0.7          # relaxation times
rhoA = rhoB = 1.0          # densities
alpha = 0.01               # interfacial tension
beta = 0.95                # interface sharpness
capillary_number = 1e-5
timestepMax = 10_000_000
F = [0.0, 0.0, 0.0]        # body force (flow direction)
inletLayers = outletLayers = [0, 0, 5]
```

### `FlowAdaptor_db` defaults
```python
max_steady_timesteps = 200_000
min_steady_timesteps = 100_000
fractional_flow_increment = 0.1
mass_fraction_factor = 0.0002
endpoint_threshold = 0.1
```

### `Analysis_db` defaults
```python
analysis_interval = 1000
subphase_analysis_interval = 5000
restart_file = "Restart"
```

---

## Coding Conventions

- **Async callbacks**: wrap with `dcc.Loading` for user feedback during long operations
- **Background jobs** (file transfers, morphdrain runs): use Dash background callbacks with `diskcache`
- **Page modules**: register with `dash.register_page(__name__, ...)` at the top of each page file
- **Component IDs**: all IDs are string constants in `pyLBPM/dashboard/ids.py` — never hardcode strings in callbacks
- **Filesystem calls**: always use `HPCFilesystem` methods, never call `open()` / `pathlib` directly in page code

---

## Analysis Dashboard — Refactoring (March 2026)

### What was done
The analysis dashboard underwent a complete refactoring to simplify complexity and improve performance:

**1. Removed authentication backends**
- Deleted `pyLBPM/filesystem/sftp.py` (SFTP/paramiko)
- Simplified `pyLBPM/filesystem/__init__.py` to always return `LocalFilesystem`
- Dashboard now works with local file paths only

**2. Fixed callback conflicts**
- Added page-specific component IDs to `pyLBPM/dashboard/ids.py`:
  - Monitor: `MONITOR_X_VAR`, `MONITOR_Y_VAR`, `MONITOR_INTERVAL`
  - Subphase: `SUBPHASE_X_VAR`, `SUBPHASE_Y_VAR`
  - SCAL: `SCAL_X_VAR`, `SCAL_Y_VAR`
  - 3D Vis: `VIS_3D_DATA_KEY`, `VIS_3D_SUBDOMAIN`, `VIS_3D_TIMESTEP`, `VIS_3D_DOWNSAMPLE`
- All legacy pages previously shared `X_VAR_DROPDOWN`, `Y_VAR_DROPDOWN`, causing Dash callback collisions

**3. Migrated legacy pages to callback-based pattern**
- `monitor.py`, `subphase_analysis.py`, `SCAL.py`: Rewrote from import-time dataloader calls to callback-based pattern
- All pages now:
  - Load data on page visit via `dcc.Location` trigger
  - Read files via `get_filesystem()` (not raw `pathlib`)
  - Store CSV in `dcc.Store`
  - Update charts when dropdown selections change
- Monitor page added real-time polling via `dcc.Interval` (5s interval) for live simulation tracking

**4. Performance improvements**
- **Presimulation page**: Removed `PRESIM_GEOMETRY_STORE` which was base64-encoding and storing entire `.morphdrain.raw` files (up to 22 MB) in browser memory. Now reads geometry on-demand from disk when slider moves.
- **3D Visualization page**: Added startup error handling to prevent crashes when no `vis*` directories exist; shows graceful empty state instead.

**5. Removed dead code**
- Deleted `pyLBPM/dashboard/pages/pyvista_dash.py` (unregistered prototype)
- Removed unused layout functions: `create_presim_layout()`, `create_linechart_layout()`
- Removed unused plotter functions: `render_morphdrain_linechart()`, `render_slice()`, `render_linechart()`

### Pattern to follow for new pages
```python
from dash import dcc, Input, Output, callback, html
from pyLBPM.filesystem import get_filesystem
from pyLBPM.dashboard import ids

# Page layout
layout = dbc.Container([
    dcc.Location(id="page-location", refresh=False),  # trigger on page load
    dcc.Store(id=ids.YOUR_CSV_STORE),  # store CSV data
    html.Div(id="your-controls"),  # dropdowns etc.
    dcc.Graph(id="your-chart"),
])

@callback(
    Output(ids.YOUR_CSV_STORE, "data"),
    Output(ids.YOUR_DROPDOWN, "options"),
    Input("page-location", "pathname"),
)
def load_data(_pathname):
    fs = get_filesystem()
    csv_bytes = fs.read_file(csv_path)
    df = pd.read_csv(pd.io.common.StringIO(csv_bytes.decode("utf-8")), sep=r"\s+")
    return df.to_dict("records"), [{"label": col, "value": col} for col in df.columns]

@callback(
    Output("your-chart", "figure"),
    Input(ids.YOUR_DROPDOWN, "value"),
    State(ids.YOUR_CSV_STORE, "data"),
    prevent_initial_call=True,
)
def update_chart(x_col, records):
    if not records or not x_col:
        return px.line(title="Select data to plot")
    df = pd.DataFrame(records)
    return px.line(df, y=x_col)
```

---

## Running Tests

```bash
pytest tests/
```

Test data (including a sample `input.db`) is in `tests/`.
