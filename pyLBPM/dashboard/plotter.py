import numpy as np
import dash_vtk
from dash_vtk.utils import to_mesh_state, to_volume_state

try:
    # VTK 9+
    from vtkmodules.vtkImagingCore import vtkRTAnalyticSource
except ImportError:
    # VTK =< 8
    from vtk.vtkImagingCore import vtkRTAnalyticSource

import plotly.express as px
from pyLBPM.dashboard import dataloader


def render_phase_isosurfaces(image_volume: np.ndarray) -> dash_vtk.View:
    """Render phase field as two isosurfaces (solid/NWP and NWP/WP boundaries)."""
    nx, ny, nz = image_volume.shape
    cx, cy, cz = nx / 2, ny / 2, nz / 2
    dist = max(nx, ny, nz) * 2.0

    return dash_vtk.View(
        children=[
            _get_mesh(
                image_volume=image_volume,
                iso_value=0.5,
                property={"edgeVisibility": False, "opacity": 0.2, "color": (168/255, 215/255, 1)},
                showCubeAxes=True,
                cubeAxesStyle={"axisLabels": ["X", "Y", "Z"]},
            ),
            _get_mesh(
                image_volume=image_volume,
                iso_value=1.5,
                property={"edgeVisibility": False, "opacity": 0.8, "color": (0.08, 0.50, 0.00)},
                showCubeAxes=False,
                cubeAxesStyle={"axisLabels": ["", "", ""]},
                add_padding=True,
            ),
        ],
        background=[1, 1, 1],
        cameraPosition=[cx, cy, cz + dist],
        cameraViewUp=[0, 1, 0],
    )


def render_volume(image_volume: np.ndarray) -> dash_vtk.View:
    """Render data as a volume."""
    nx, ny, nz = image_volume.shape
    cx, cy, cz = nx / 2, ny / 2, nz / 2
    dist = max(nx, ny, nz) * 2.0

    return dash_vtk.View(
        children=[
            _get_volume(image_volume=image_volume),
        ],
        background=[1, 1, 1],
        cameraPosition=[cx, cy, cz + dist],
        cameraViewUp=[0, 1, 0],
    )



def _get_mesh(image_volume: np.ndarray, iso_value: float, add_padding=False, **kwargs) -> dash_vtk.GeometryRepresentation:
    vol = image_volume.astype(np.float32)
    if add_padding:
        vol = np.pad(vol, ((1, 1), (1, 1), (1, 1)), constant_values=0)

    vol_obj = dataloader._wrap_numpy_to_vtk(vol)
    contour = vol_obj.contour(isosurfaces=[iso_value])

    mesh_state = to_mesh_state(contour)

    geom = dash_vtk.GeometryRepresentation(
        children=[
            dash_vtk.Mesh(state=mesh_state)
        ],
        **kwargs
    )

    return geom


def _get_volume(image_volume: np.ndarray, **kwargs) -> dash_vtk.GeometryRepresentation:
    geom = dash_vtk.VolumeDataRepresentation(
        spacing=[1, 1, 1],
        dimensions=image_volume.shape,
        origin=[0, 0, 0],
        scalars=image_volume.flatten(order="F"),
        rescaleColorMap=False,
        colorMapPreset="Cool to Warm",
        **kwargs
    )

    return geom
