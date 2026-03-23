from dash import html, dcc
import pathlib
from pyLBPM.dashboard import ids, widgets
import dash_bootstrap_components as dbc
import pandas as pd


def create_filenotfound_layout(page_title, class_name: str="app-div", id_str: str="file-not-found") -> html.Div:
    required_files = {
        "Input File": "input.db",
        "Pre-Simulation": "morphdrain.csv and *.morphdrain.raw",
        "Timelog Monitoring": "timelog.csv",
        "SCAL Analysis": "SCAL.csv",
        "Subphase Analysis": "subphase.csv",
        "3D Visualization": "id_t*.raw or vis*/*.h5"
    }


    return html.Div(
        className=class_name,
        children=[
            html.Hr(),
            html.H6("Could not find the files needed to display this page."),
            html.H6(f"This page requires {required_files.get(page_title)}"),
        ],
        id=id_str
    )
