import pathlib
import numpy as np
import pandas as pd
from dash import html, dcc, callback, Input, Output
import dash_vtk
from dash_vtk.utils import to_mesh_state, to_volume_state

try:
    # VTK 9+
    from vtkmodules.vtkImagingCore import vtkRTAnalyticSource
except ImportError:
    # VTK =< 8
    from vtk.vtkImagingCore import vtkRTAnalyticSource

import plotly.express as px
from pyLBPM.dashboard import ids, dataloader


def render_morphdrain_linechart(data: pd.DataFrame, LINE_CHART_ID: str) -> html.Div:
    fig = px.line(data, x="sw", y="radius")
    return html.Div(dcc.Graph(figure=fig), id=LINE_CHART_ID)

def render_slice(simulation_dir: pathlib.Path, IMAGE_SLICE_ID: str) -> html.Div:
    try:
        morphdrain_file = list(simulation_dir.glob("*.morphdrain.raw"))[0]
        img = dataloader.raw_reader(simulation_dir=simulation_dir, raw_file=morphdrain_file.name,
                                    img_shape=(256, 256, 256), data_type=np.uint8)

        fig = px.imshow(img[img.shape[0]//2, :, :])
        fig.update_coloraxes(colorbar_x=0.8)

        return html.Div(dcc.Graph(figure=fig), id=IMAGE_SLICE_ID)
    except IndexError:
        raise FileNotFoundError


def render_linechart(data: pd.DataFrame, LINE_CHART_ID: str) -> html.Div:
    @callback(
        Output(LINE_CHART_ID, "children"),

        [Input(ids.X_VAR_DROPDOWN, "value"),
         Input(ids.Y_VAR_DROPDOWN, "value")],
    )
    def update_line_chart(x_var: list[str], y_var: list[str]) -> html.Div:
        if isinstance(y_var, list) and len(y_var) == 1:
            y_var = y_var[0]

        if len([x_var]) == 0 or len([*y_var]) == 0:
            return html.Div("No data selected", id=LINE_CHART_ID)

        fig = px.line(data, x=x_var, y=y_var, template="plotly_white")
        return html.Div(dcc.Graph(figure=fig),
                        id=LINE_CHART_ID,
                        style={"width": "100%", "height": "450px",})

    return html.Div(id=LINE_CHART_ID)


def render_3d_vis(simulation_dir: pathlib.Path, timesteps: list[int], VTK_VIS_ID: str) -> html.Div:
    @callback(
        Output(VTK_VIS_ID, "children"),
        [Input(ids.X_VAR_DROPDOWN, "value"),
         Input(ids.SINGLE_DROPDOWN, "value"),
         Input(ids.SLIDER, "value")],
    )
    def update_3d_vis(datakey: str, subdomains: list[str], slider_step: int) -> html.Div:
        # Get the timestep from the slider
        sim_step = timesteps[slider_step]*1000
        # print(sim_step)

        # TODO: Add callback with data keys to plot
        # # Open the VTK files
        # img = dataloader.h5_reader(simulation_dir=simulation_dir / f"vis{sim_step}",
        #                      subdomain_num='all', data_key='phase')
        if "all" in subdomains:
            subdomains = "all"

        img = dataloader.h5_reader(simulation_dir=simulation_dir / f"vis{sim_step}",
                                    subdomain_num=subdomains, data_key=datakey)

        # except IndexError:
        #     print("No hdf5 files found, searching for raw files...")
        #     img = dataloader.raw_reader(simulation_dir=simulation_dir, raw_file=f"id_t{sim_step}.raw",
        #                                 img_shape=(256, 256, 256), data_type=np.uint8)

        # TODO: Add callback to get other phase contours
        if datakey.lower() == "phase":
            geom_plot = dash_vtk.View(
                children=[
                    _get_mesh(image_volume=img, phase_val=0,
                              property={"edgeVisibility": False, "opacity": 0.2, "color": (168/255, 215/255, 1)},
                              showCubeAxes=False,
                              cubeAxesStyle={"axisLabels": ["", "", ""]},
                              ),
                    _get_mesh(image_volume=img, phase_val=1,
                              property={"edgeVisibility": False, "opacity": 1, "color": (0.08, 0.50, 0.00)},#(191/255, 87/255, 0)},#,
                              showCubeAxes=False,
                              cubeAxesStyle={"axisLabels": ["", "", ""]},
                              add_padding=True
                              ),
                ],
                background=[1, 1, 1],
                cameraPosition=[1, 1, 1],
            )
        else:
            geom_plot = dash_vtk.View(
                children=[
                    _get_volume(image_volume=img,
                                # property={"edgeVisibility": False, "opacity": 1},
                                # showCubeAxes=False,
                                # cubeAxesStyle={"axisLabels": ["", "", ""]},
                                ),
                ],
                background=[1, 1, 1],
                cameraPosition=[1, 1, 1],
            )



        return html.Div(
            style={"width": "100%", "height": "600px"},
            children=[
                geom_plot,
            ],
            id=VTK_VIS_ID
        )
    return html.Div(id=VTK_VIS_ID)


def _get_mesh(image_volume: np.ndarray, phase_val: int, add_padding=False, **kwargs) -> dash_vtk.GeometryRepresentation:
    phase_vol = (image_volume == phase_val).astype(np.uint8)
    if add_padding:
        phase_vol = np.pad(phase_vol, ((1, 1), (1, 1), (1, 1)), constant_values=0)

    phase_vol_obj = dataloader._wrap_numpy_to_vtk(phase_vol)
    phase_contour = phase_vol_obj.contour(isosurfaces=[0.1])

    mesh_state = to_mesh_state(phase_contour)

    geom = dash_vtk.GeometryRepresentation(
        children=[
            dash_vtk.Mesh(state=mesh_state)
        ],
        **kwargs
    )

    return geom


def _get_volume(image_volume: np.ndarray, **kwargs) -> dash_vtk.GeometryRepresentation:

    # vol_obj = dataloader._wrap_numpy_to_vtk(image_volume)
    # # phase_contour = vol_obj.contour(isosurfaces=[0.1])
    #
    # vol_state = to_volume_state(vol_obj)
    print(image_volume)

    geom = dash_vtk.VolumeDataRepresentation(
        spacing=[1, 1, 1],
        dimensions=image_volume.shape,
        origin=[0, 0, 0],
        scalars=image_volume.flatten(order="F"),
        rescaleColorMap=False,
        # children=[
        #     dash_vtk.VolumeController(),
        #     dash_vtk.Volume(state=vol_state)
        # ],
        **kwargs
    )

    return geom







