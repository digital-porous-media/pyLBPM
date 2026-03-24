"""Helper module to generate standalone Python scripts for recreating dashboard plots."""

from pathlib import Path


def monitor_script(sim_dir: str, x_col: str, y_cols) -> str:
    """Generate a standalone script for monitor plot (Plotly backend).

    Args:
        sim_dir: Path to simulation directory
        x_col: X-axis column name
        y_cols: Y-axis column name(s) - string or list of strings
    """
    # Handle both single column and list of columns
    if isinstance(y_cols, str):
        y_cols = [y_cols]

    y_list_str = ", ".join(f'"{col}"' for col in y_cols)
    return f'''#!/usr/bin/env python
"""Auto-generated monitor plot script from pyLBPM analysis dashboard."""

import pandas as pd
import plotly.io as pio
import plotly.express as px
from pathlib import Path

pio.renderers.default = "browser"

sim_dir = Path(r"{sim_dir}")
csv_path = sim_dir / "timelog.csv"

# Load data
df = pd.read_csv(csv_path, sep=r"\\s+")

# Add synthetic step column (matches dashboard behavior)
df["sim.step"] = range(len(df))

# Create plot
fig = px.line(df, x="{x_col}", y=[{y_list_str}],
              title="Monitor Plot", markers=True)
fig.update_layout(
    template="plotly_white",
    font=dict(size=12),
    height=600,
    hovermode="x unified",
)

# Display plot
fig.show()
'''


def monitor_script_matplotlib(sim_dir: str, x_col: str, y_cols) -> str:
    """Generate a standalone script for monitor plot (Matplotlib backend).

    Args:
        sim_dir: Path to simulation directory
        x_col: X-axis column name
        y_cols: Y-axis column name(s) - string or list of strings
    """
    # Handle both single column and list of columns
    if isinstance(y_cols, str):
        y_cols = [y_cols]

    # Generate plot lines for each column
    plot_lines = "\n".join(f'plt.plot(df["{x_col}"], df["{col}"], marker="o", markersize=3, label="{col}")'
                          for col in y_cols)

    return f'''#!/usr/bin/env python
"""Auto-generated monitor plot script from pyLBPM analysis dashboard."""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

sim_dir = Path(r"{sim_dir}")
csv_path = sim_dir / "timelog.csv"

# Load data
df = pd.read_csv(csv_path, sep=r"\\s+")

# Add synthetic step column (matches dashboard behavior)
df["sim.step"] = range(len(df))

# Create plot
plt.figure(figsize=(10, 6))
{plot_lines}
plt.xlabel("{x_col}")
plt.ylabel("Values")
plt.title("Monitor Plot")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()
'''


def subphase_script(sim_dir: str, x_col: str, y_cols) -> str:
    """Generate a standalone script for subphase analysis plot (Plotly backend).

    Args:
        sim_dir: Path to simulation directory
        x_col: X-axis column name
        y_cols: Y-axis column name(s) - string or list of strings
    """
    # Handle both single column and list of columns
    if isinstance(y_cols, str):
        y_cols = [y_cols]

    y_list_str = ", ".join(f'"{col}"' for col in y_cols)
    return f'''#!/usr/bin/env python
"""Auto-generated subphase analysis plot script from pyLBPM analysis dashboard."""

import pandas as pd
import plotly.io as pio
import plotly.express as px
from pathlib import Path

pio.renderers.default = "browser"

sim_dir = Path(r"{sim_dir}")
csv_path = sim_dir / "subphase.csv"

# Load data
df = pd.read_csv(csv_path, sep=r"\\s+")

# Add synthetic step column (matches dashboard behavior)
df["sim.step"] = range(len(df))

# Create plot
fig = px.line(df, x="{x_col}", y=[{y_list_str}],
              title="Subphase Analysis", markers=True)
fig.update_layout(
    template="plotly_white",
    font=dict(size=12),
    height=600,
    hovermode="x unified",
)

# Display plot
fig.show()
'''


def subphase_script_matplotlib(sim_dir: str, x_col: str, y_cols) -> str:
    """Generate a standalone script for subphase analysis plot (Matplotlib backend).

    Args:
        sim_dir: Path to simulation directory
        x_col: X-axis column name
        y_cols: Y-axis column name(s) - string or list of strings
    """
    # Handle both single column and list of columns
    if isinstance(y_cols, str):
        y_cols = [y_cols]

    # Generate plot lines for each column
    plot_lines = "\n".join(f'plt.plot(df["{x_col}"], df["{col}"], marker="o", markersize=3, label="{col}")'
                          for col in y_cols)

    return f'''#!/usr/bin/env python
"""Auto-generated subphase analysis plot script from pyLBPM analysis dashboard."""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

sim_dir = Path(r"{sim_dir}")
csv_path = sim_dir / "subphase.csv"

# Load data
df = pd.read_csv(csv_path, sep=r"\\s+")

# Add synthetic step column (matches dashboard behavior)
df["sim.step"] = range(len(df))

# Create plot
plt.figure(figsize=(10, 6))
{plot_lines}
plt.xlabel("{x_col}")
plt.ylabel("Values")
plt.title("Subphase Analysis")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()
'''


def scal_script(sim_dir: str, x_col: str, y_cols) -> str:
    """Generate a standalone script for SCAL analysis plot (Plotly backend).

    Args:
        sim_dir: Path to simulation directory
        x_col: X-axis column name
        y_cols: Y-axis column name(s) - string or list of strings
    """
    # Handle both single column and list of columns
    if isinstance(y_cols, str):
        y_cols = [y_cols]

    y_list_str = ", ".join(f'"{col}"' for col in y_cols)
    return f'''#!/usr/bin/env python
"""Auto-generated SCAL analysis plot script from pyLBPM analysis dashboard."""

import pandas as pd
import plotly.io as pio
import plotly.express as px
from pathlib import Path

pio.renderers.default = "browser"

sim_dir = Path(r"{sim_dir}")
csv_path = sim_dir / "SCAL.csv"

# Load data
df = pd.read_csv(csv_path, sep=r"\\s+")

# Add synthetic step column (matches dashboard behavior)
df["sim.step"] = range(len(df))

# Create plot
fig = px.line(df, x="{x_col}", y=[{y_list_str}],
              title="SCAL Analysis", markers=True)
fig.update_layout(
    template="plotly_white",
    font=dict(size=12),
    height=600,
    hovermode="x unified",
)

# Display plot
fig.show()
'''


def scal_script_matplotlib(sim_dir: str, x_col: str, y_cols) -> str:
    """Generate a standalone script for SCAL analysis plot (Matplotlib backend).

    Args:
        sim_dir: Path to simulation directory
        x_col: X-axis column name
        y_cols: Y-axis column name(s) - string or list of strings
    """
    # Handle both single column and list of columns
    if isinstance(y_cols, str):
        y_cols = [y_cols]

    # Generate plot lines for each column
    plot_lines = "\n".join(f'plt.plot(df["{x_col}"], df["{col}"], marker="o", markersize=3, label="{col}")'
                          for col in y_cols)

    return f'''#!/usr/bin/env python
"""Auto-generated SCAL analysis plot script from pyLBPM analysis dashboard."""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

sim_dir = Path(r"{sim_dir}")
csv_path = sim_dir / "SCAL.csv"

# Load data
df = pd.read_csv(csv_path, sep=r"\\s+")

# Add synthetic step column (matches dashboard behavior)
df["sim.step"] = range(len(df))

# Create plot
plt.figure(figsize=(10, 6))
{plot_lines}
plt.xlabel("{x_col}")
plt.ylabel("Values")
plt.title("SCAL Analysis")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()
'''


def presimulation_csv_script(sim_dir: str, x_col: str, y_col: str) -> str:
    """Generate a standalone script for presimulation (morphdrain) CSV plot (Plotly backend)."""
    return f'''#!/usr/bin/env python
"""Auto-generated morphological drainage plot script from pyLBPM analysis dashboard."""

import pandas as pd
import plotly.io as pio
import plotly.express as px
from pathlib import Path

pio.renderers.default = "browser"

sim_dir = Path(r"{sim_dir}")
csv_path = sim_dir / "morphdrain.csv"

# Load data
df = pd.read_csv(csv_path, sep=r"\\s+")

# Create plot
fig = px.line(df, x="{x_col}", y="{y_col}",
              title="Morphological Drainage Analysis", markers=True)
fig.update_layout(
    template="plotly_white",
    font=dict(size=12),
    height=600,
    hovermode="x unified",
)

# Display plot
fig.show()
'''


def presimulation_csv_script_matplotlib(sim_dir: str, x_col: str, y_col: str) -> str:
    """Generate a standalone script for presimulation (morphdrain) CSV plot (Matplotlib backend)."""
    return f'''#!/usr/bin/env python
"""Auto-generated morphological drainage plot script from pyLBPM analysis dashboard."""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

sim_dir = Path(r"{sim_dir}")
csv_path = sim_dir / "morphdrain.csv"

# Load data
df = pd.read_csv(csv_path, sep=r"\\s+")

# Create plot
plt.figure(figsize=(10, 6))
plt.plot(df["{x_col}"], df["{y_col}"], marker="o", markersize=3, label="{y_col}")
plt.xlabel("{x_col}")
plt.ylabel("{y_col}")
plt.title("Morphological Drainage Analysis")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()
'''


def presimulation_slice_script(sim_dir: str, raw_file: str, axis: int, slice_idx: int) -> str:
    """Generate a standalone script for presimulation geometry slice (Plotly backend)."""
    axis_names = {0: "X (yz-plane)", 1: "Y (xz-plane)", 2: "Z (xy-plane)"}
    axis_name = axis_names.get(axis, str(axis))

    return f'''#!/usr/bin/env python
"""Auto-generated geometry slice visualization script from pyLBPM analysis dashboard."""

import numpy as np
import plotly.io as pio
import plotly.express as px
from pathlib import Path

pio.renderers.default = "browser"

sim_dir = Path(r"{sim_dir}")
raw_path = sim_dir / "{raw_file}"

# Load raw binary geometry
with open(raw_path, "rb") as f:
    data = np.fromfile(f, dtype=np.uint8)

# Determine shape (cubic assumption)
n3 = len(data)
n = round(n3 ** (1/3))
assert n ** 3 == n3, f"File size {{n3}} does not correspond to cubic geometry"

arr = data.reshape((n, n, n))

# Take 2D slice along axis {axis}
axis = {axis}
slice_idx = {slice_idx}

if axis == 0:
    slice_arr = arr[slice_idx, :, :]
elif axis == 1:
    slice_arr = arr[:, slice_idx, :]
else:  # axis == 2
    slice_arr = arr[:, :, slice_idx]

# Create plot
fig = px.imshow(
    slice_arr,
    color_continuous_scale="gray",
    aspect="equal",
    title=f"Geometry Slice - {axis_name} (index {{slice_idx}})",
)
fig.update_layout(
    template="plotly_white",
    font=dict(size=12),
    height=600,
)

# Display plot
fig.show()
'''


def presimulation_slice_script_matplotlib(sim_dir: str, raw_file: str, axis: int, slice_idx: int) -> str:
    """Generate a standalone script for presimulation geometry slice (Matplotlib backend)."""
    axis_names = {0: "X (yz-plane)", 1: "Y (xz-plane)", 2: "Z (xy-plane)"}
    axis_name = axis_names.get(axis, str(axis))

    return f'''#!/usr/bin/env python
"""Auto-generated geometry slice visualization script from pyLBPM analysis dashboard."""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

sim_dir = Path(r"{sim_dir}")
raw_path = sim_dir / "{raw_file}"

# Load raw binary geometry
with open(raw_path, "rb") as f:
    data = np.fromfile(f, dtype=np.uint8)

# Determine shape (cubic assumption)
n3 = len(data)
n = round(n3 ** (1/3))
assert n ** 3 == n3, f"File size {{n3}} does not correspond to cubic geometry"

arr = data.reshape((n, n, n))

# Take 2D slice along axis {axis}
axis = {axis}
slice_idx = {slice_idx}

if axis == 0:
    slice_arr = arr[slice_idx, :, :]
elif axis == 1:
    slice_arr = arr[:, slice_idx, :]
else:  # axis == 2
    slice_arr = arr[:, :, slice_idx]

# Create plot
plt.figure(figsize=(8, 8))
plt.imshow(slice_arr, cmap="gray", aspect="equal")
plt.colorbar(label="Value")
plt.title(f"Geometry Slice - {axis_name} (index {{slice_idx}})")
plt.xlabel("Y" if axis == 0 else "X" if axis == 1 else "X")
plt.ylabel("Z" if axis == 0 else "Z" if axis == 1 else "Y")
plt.tight_layout()
plt.show()
'''


def vis_2d_script(sim_dir: str, data_key: str, timestep: int, axis: int, slice_idx: int,
                  downsample: int, input_filename: str = "input.db") -> str:
    """Generate a standalone script for 2D slice visualization (Plotly backend)."""
    axis_names = {0: "X (yz-plane)", 1: "Y (xz-plane)", 2: "Z (xy-plane)"}
    axis_name = axis_names.get(axis, str(axis))
    colorscale = "Turbo" if data_key != "phase configurations" else "RdBu"

    if data_key == "phase configurations":
        return f'''#!/usr/bin/env python
"""Auto-generated 2D slice visualization script from pyLBPM analysis dashboard."""

import numpy as np
import plotly.io as pio
import plotly.express as px
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

pio.renderers.default = "browser"

from pyLBPM.dashboard import dataloader

sim_dir = Path(r"{sim_dir}")
timestep = {timestep}
downsample = {downsample}
axis = {axis}
slice_idx = {slice_idx}
input_filename = "{input_filename}"

# Get domain dimensions from input.db
nx, ny, nz = dataloader.get_domain_dims(sim_dir, input_filename=input_filename)

# Load raw phase file
img = dataloader.raw_reader(
    simulation_dir=sim_dir,
    raw_file=f"id_t{{timestep}}.raw",
    img_shape=(nx, ny, nz),
    data_type=np.uint8
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

# Create plot
fig = px.imshow(
    slice_arr,
    color_continuous_scale="{colorscale}",
    aspect="equal",
    title=f"Phase Configuration (id_t{{timestep}}) - Slice {{slice_idx}} along Axis {axis}",
)
fig.update_layout(
    template="plotly_white",
    font=dict(size=12),
    height=600,
    xaxis_title="",
    yaxis_title="",
)

# Display plot
fig.show()
'''
    else:
        return f'''#!/usr/bin/env python
"""Auto-generated 2D slice visualization script from pyLBPM analysis dashboard."""

import numpy as np
import plotly.io as pio
import plotly.express as px
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

pio.renderers.default = "browser"

from pyLBPM.dashboard import dataloader

sim_dir = Path(r"{sim_dir}")
timestep = {timestep}
downsample = {downsample}
axis = {axis}
slice_idx = {slice_idx}
data_key = "{data_key}"
input_filename = "{input_filename}"

# Load HDF5 data
img = dataloader.h5_reader(
    simulation_dir=sim_dir / f"vis{{timestep}}",
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

# Create plot
fig = px.imshow(
    slice_arr,
    color_continuous_scale="{colorscale}",
    aspect="equal",
    title=f"{{data_key}} (vis{{timestep}}) - Slice {{slice_idx}} along Axis {axis}",
)
fig.update_layout(
    template="plotly_white",
    font=dict(size=12),
    height=600,
    xaxis_title="",
    yaxis_title="",
)

# Display plot
fig.show()
'''


def vis_2d_script_matplotlib(sim_dir: str, data_key: str, timestep: int, axis: int, slice_idx: int,
                             downsample: int, input_filename: str = "input.db") -> str:
    """Generate a standalone script for 2D slice visualization (Matplotlib backend)."""
    axis_names = {0: "X (yz-plane)", 1: "Y (xz-plane)", 2: "Z (xy-plane)"}
    axis_name = axis_names.get(axis, str(axis))
    colormap = "turbo" if data_key != "phase configurations" else "RdBu"

    if data_key == "phase configurations":
        return f'''#!/usr/bin/env python
"""Auto-generated 2D slice visualization script from pyLBPM analysis dashboard."""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from pyLBPM.dashboard import dataloader

sim_dir = Path(r"{sim_dir}")
timestep = {timestep}
downsample = {downsample}
axis = {axis}
slice_idx = {slice_idx}
input_filename = "{input_filename}"

# Get domain dimensions from input.db
nx, ny, nz = dataloader.get_domain_dims(sim_dir, input_filename=input_filename)

# Load raw phase file
img = dataloader.raw_reader(
    simulation_dir=sim_dir,
    raw_file=f"id_t{{timestep}}.raw",
    img_shape=(nx, ny, nz),
    data_type=np.uint8
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

# Create plot
plt.figure(figsize=(10, 8))
plt.imshow(slice_arr, cmap="{colormap}", aspect="equal")
plt.colorbar(label="Phase Value")
plt.title(f"Phase Configuration (id_t{{timestep}}) - Slice {{slice_idx}} along Axis {axis}")
plt.xlabel("Y" if axis == 0 else "X" if axis == 1 else "X")
plt.ylabel("Z" if axis == 0 else "Z" if axis == 1 else "Y")
plt.tight_layout()
plt.show()
'''
    else:
        return f'''#!/usr/bin/env python
"""Auto-generated 2D slice visualization script from pyLBPM analysis dashboard."""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from pyLBPM.dashboard import dataloader

sim_dir = Path(r"{sim_dir}")
timestep = {timestep}
downsample = {downsample}
axis = {axis}
slice_idx = {slice_idx}
data_key = "{data_key}"
input_filename = "{input_filename}"

# Load HDF5 data
img = dataloader.h5_reader(
    simulation_dir=sim_dir / f"vis{{timestep}}",
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

# Create plot
plt.figure(figsize=(10, 8))
plt.imshow(slice_arr, cmap="{colormap}", aspect="equal")
plt.colorbar(label="Data Value")
plt.title(f"{{data_key}} (vis{{timestep}}) - Slice {{slice_idx}} along Axis {axis}")
plt.xlabel("Y" if axis == 0 else "X" if axis == 1 else "X")
plt.ylabel("Z" if axis == 0 else "Z" if axis == 1 else "Y")
plt.tight_layout()
plt.show()
'''


def vis_3d_script(sim_dir: str, data_key: str, timestep: int, subdomains: list,
                  downsample: int, input_filename: str = "input.db") -> str:
    """Generate a standalone script for 3D visualization using PyVista."""
    subdomains_str = repr(subdomains)

    if data_key == "phase configurations":
        return f'''#!/usr/bin/env python
"""Auto-generated 3D visualization script from pyLBPM analysis dashboard."""

import numpy as np
import pyvista as pv
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from pyLBPM.dashboard import dataloader

sim_dir = Path(r"{sim_dir}")
timestep = {timestep}
downsample = {downsample}
input_filename = "{input_filename}"

# Get domain dimensions from input.db
nx, ny, nz = dataloader.get_domain_dims(sim_dir, input_filename=input_filename)

# Load raw phase file
img = dataloader.raw_reader(
    simulation_dir=sim_dir,
    raw_file=f"id_t{{timestep}}.raw",
    img_shape=(nx, ny, nz),
    data_type=np.uint8
)

# Apply downsample
img = img[::downsample, ::downsample, ::downsample]

# Create PyVista plotter
pl = pv.Plotter(notebook=False)
pl.set_background("white")

# Render isosurfaces
vol = img.astype(np.float32)
vol_obj = pv.wrap(vol)

# Solid/NWP boundary (iso_value=0.5) - light blue
mesh1 = vol_obj.contour(isosurfaces=[0.5])
pl.add_mesh(mesh1, color=(168/255, 215/255, 1.0), opacity=0.2, label="Solid/NWP")

# NWP/WP boundary (iso_value=1.5) - green
vol_padded = np.pad(vol, ((1, 1), (1, 1), (1, 1)), constant_values=0)
vol_padded_obj = pv.wrap(vol_padded)
mesh2 = vol_padded_obj.contour(isosurfaces=[1.5])
pl.add_mesh(mesh2, color=(0.08, 0.50, 0.00), opacity=0.8, label="NWP/WP")

# Set camera to center of domain
nx_ds = nx // downsample
ny_ds = ny // downsample
nz_ds = nz // downsample
cx, cy, cz = nx_ds / 2, ny_ds / 2, nz_ds / 2
dist = max(nx_ds, ny_ds, nz_ds) * 2.0
pl.camera.position = (cx, cy, cz + dist)
pl.camera.focal_point = (cx, cy, cz)
pl.camera.view_up = (0, 1, 0)

pl.show()
'''
    else:
        # Determine colormap and color limits based on data_key
        key_lower = data_key.lower()
        if "phase" in key_lower:
            cmap_import = "from matplotlib.colors import LinearSegmentedColormap"
            cmap_setup = (
                "# Phase data: invert and use UT orange colormap\n"
                "data = -1 * img.astype(np.float32)\n"
                "ut_cmap = LinearSegmentedColormap.from_list(\n"
                '    "ut_orange", [(1.0, 1.0, 1.0), (191/255, 87/255, 0.0)]\n'
                ")\n"
                "cmap = ut_cmap\n"
                "clim = (-1, 1)"
            )
        elif any(v in key_lower for v in ["velocity", "vel"]):
            cmap_import = "import matplotlib.pyplot as plt"
            cmap_setup = (
                "# Velocity data: diverging colormap symmetric around 0\n"
                "data = img.astype(np.float32)\n"
                "vmin, vmax = float(data.min()), float(data.max())\n"
                "abs_max = max(abs(vmin), abs(vmax))\n"
                'cmap = plt.get_cmap("coolwarm")\n'
                "clim = (-abs_max, abs_max)"
            )
        else:
            cmap_import = "import matplotlib.pyplot as plt"
            cmap_setup = (
                "# Sequential colormap over full data range\n"
                "data = img.astype(np.float32)\n"
                "vmin, vmax = float(data.min()), float(data.max())\n"
                'cmap = plt.get_cmap("viridis")\n'
                "clim = (vmin, vmax)"
            )

        return f'''#!/usr/bin/env python
"""Auto-generated 3D visualization script from pyLBPM analysis dashboard."""

import numpy as np
import pyvista as pv
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from pyLBPM.dashboard import dataloader

{cmap_import}

sim_dir = Path(r"{sim_dir}")
timestep = {timestep}
downsample = {downsample}
subdomains = {subdomains_str}
data_key = "{data_key}"
input_filename = "{input_filename}"

# Load HDF5 data
img = dataloader.h5_reader(
    simulation_dir=sim_dir / f"vis{{timestep}}",
    data_key=data_key,
    subdomain_num=subdomains,
    input_db_path=sim_dir,
    input_filename=input_filename,
)

# Apply downsample
img = img[::downsample, ::downsample, ::downsample]

# Colormap and color limit selection
{cmap_setup}

# Create PyVista plotter
pl = pv.Plotter(notebook=False)
pl.set_background("white")

# Create PyVista ImageData for volume rendering
grid = pv.ImageData()
grid.dimensions = np.array(img.shape) + 1
grid.spacing = (1.0, 1.0, 1.0)
grid.origin = (0.0, 0.0, 0.0)
grid.cell_data["values"] = data.flatten(order="F")

actor = pl.add_volume(
    grid, scalars="values", cmap=cmap, opacity="sigmoid", clim=clim
)
# Force trilinear interpolation to match VTK GPU ray casting (eliminates staircasing)
actor.GetProperty().SetInterpolationTypeToLinear()

pl.add_scalar_bar(title=data_key)

# Set camera to center of domain
nx, ny, nz = img.shape
cx, cy, cz = nx / 2, ny / 2, nz / 2
dist = max(nx, ny, nz) * 2.0
pl.camera.position = (cx, cy, cz + dist)
pl.camera.focal_point = (cx, cy, cz)
pl.camera.view_up = (0, 1, 0)

pl.show()
# To save as HTML instead: pl.export_html("output.html")
'''
