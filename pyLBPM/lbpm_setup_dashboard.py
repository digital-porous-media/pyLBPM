"""Pre-simulation Setup Dashboard entry point.

Run with:
    python -m pyLBPM.lbpm_setup_dashboard

Or directly:
    python pyLBPM/lbpm_setup_dashboard.py
"""

import sys
import dash
import dash_bootstrap_components as dbc
from dash import Dash, html
from dash_bootstrap_components.themes import BOOTSTRAP


def main() -> None:
    app = Dash(
        __name__,
        external_stylesheets=[BOOTSTRAP],
        use_pages=True,
        pages_folder="dashboard/setup_pages",
        suppress_callback_exceptions=True,
    )

    sidebar = dbc.Nav(
        [
            dbc.NavLink(
                html.Div(page["name"], className="ms-2"),
                href=page["path"],
                active="exact",
            )
            for page in dash.page_registry.values()
        ],
        vertical=True,
        pills=True,
        className="bg-light",
    )

    app.layout = dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(html.Div()),
                    dbc.Col(
                        html.Div(
                            "LBPM Pre-Simulation Setup",
                            style={"fontSize": 30, "textAlign": "center"},
                        )
                    ),
                    dbc.Col(
                        html.Div(
                            className="external-links",
                            children=[
                                html.A(
                                    html.Img(
                                        src="https://github.com/fluidicon.png",
                                        alt="github",
                                        height=25,
                                    ),
                                    href="https://github.com/OPM/LBPM",
                                    target="_blank",
                                    style={"margin": "0px 15px"},
                                ),
                                html.A(
                                    "Docs",
                                    href="https://lbpm-sim.org/",
                                    target="_blank",
                                    style={"color": "#EEE", "margin": "0px 15px"},
                                ),
                            ],
                            style={"textAlign": "right"},
                        )
                    ),
                ],
                justify="end",
                align="center",
                style={"background-color": "#222222", "color": "#EEEEEE", "padding": "8px"},
            ),

            html.Hr(),

            dbc.Row(
                [
                    dbc.Col([sidebar], xs=4, sm=4, md=2, lg=2, xl=2, xxl=2),
                    dbc.Col([dash.page_container], xs=8, sm=8, md=10, lg=10, xl=10, xxl=10),
                ]
            ),
        ],
        fluid=True,
    )

    app.run(debug=True)


if __name__ == "__main__":
    main()
