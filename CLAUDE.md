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
| 2 | Morphological Pre-Analysis | `morphdrain.py` | View/trigger morphological drainage analysis |

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

Available backends (implemented in `pyLBPM/filesystem/`):
- `local` — wraps `pathlib.Path` (default for development); `local.py`
- `sftp` — SSH/SFTP via `paramiko` (for direct TACC access); `sftp.py`
- `tapis` — Tapis v3 Files API via `tapipy` *(planned, not yet implemented)*
- `globus` — Globus SDK (best for large file transfers) *(planned, not yet implemented)*

Backend is configured in `~/.pyLBPM/config.yml`:
```yaml
filesystem:
  backend: local   # local | sftp | tapis | globus

  # SFTP options:
  host: login1.tacc.utexas.edu
  username: myuser
  key_file: ~/.ssh/id_rsa

  # Tapis options:
  base_url: https://tacc.tapis.io
  tenant: tacc
  token: <your-token>

  # Globus options:
  source_endpoint: <your-globus-endpoint-id>
```

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

## Running Tests

```bash
pytest tests/
```

Test data (including a sample `input.db`) is in `tests/`.
