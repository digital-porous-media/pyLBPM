import pathlib
import re

import dash
from dash import html

import dash_vtk
from dash_vtk.utils import to_mesh_state

from pyLBPM.dashboard import ids, layouts, dataloader

try:
    # VTK 9+
    from vtkmodules.vtkImagingCore import vtkRTAnalyticSource
except ImportError:
    # VTK =< 8
    from vtk.vtkImagingCore import vtkRTAnalyticSource

dash.register_page(__name__, name="3D Visualization", order=5)

def get_3d_vis_layout(sim_dir, vis_dir_list):
    # Extract directory names
    vis_dir_list = [vis_dir.name for vis_dir in vis_dir_list]
    timesteps = [int(re.findall(r"\d+", vis_dir)[0]) // 1000 for vis_dir in vis_dir_list]
    timesteps = sorted(timesteps)
    vis_dir = list(sim_dir.glob("vis*/summary.xmf"))[0]
    data_keys = dataloader._get_data_keys(vis_dir)
    grid_names, _ = dataloader._get_grid_names(vis_dir)
    grid_names.append("all")

    # image_fields = dataloader.get_vis_fields(sim_dir / vis_dir_list[0] / "00000.h5")

    return layouts.create_3D_vis_layout(simulation_dir=sim_dir, timesteps=timesteps, dropdown_cats=data_keys,
                                        subdomains=grid_names,
                                        page_title="3D Visualization",
                                        class_name="3d-vis-div",
                                        plot_id=ids.VTK_3D_VIS)

sim_dir = dataloader.get_sim_dir()
vis_dir_list = list(sim_dir.glob("vis*"))
layout = get_3d_vis_layout(sim_dir, vis_dir_list)