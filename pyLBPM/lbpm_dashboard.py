import sys

sys.path.append("..")
from dash import Dash, html, dcc
import dash
import dash_bootstrap_components as dbc
from dash_bootstrap_components.themes import BOOTSTRAP
from pyLBPM.dashboard import ids


def main() -> None:

    app = Dash(__name__, external_stylesheets=[BOOTSTRAP], use_pages=True, pages_folder="dashboard/pages")

    sidebar = dbc.Nav(
        [
            dbc.NavLink(
                [
                    html.Div(page["name"], className="ms-2"),
                ],
                href=page["path"],
                active="exact"
            )
            for page in dash.page_registry.values()
        ],
        vertical=True,
        pills=True,
        className="p-2",
        style={"backgroundColor": "#f1f3f5", "borderRight": "1px solid #dee2e6"}
    )

    app.layout = dbc.Container([
        dcc.Store(id=ids.APP_INPUT_FILE_PATH, storage_type="session"),
        dbc.Row([
            dbc.Col(html.Div()),
            dbc.Col(html.Div("LBPM Simulation Dashboard",
                             style={'fontSize': 35, 'textAlign': 'center'})),
            # dbc.Col(html.Div(html.H6("Hello!")))

            dbc.Col(html.Div(
                className="external-links",
                children=[
                    html.Div(
                        children=[
                            html.A(
                                html.Img(src=dash.get_asset_url("github-mark-white.svg"), alt='github', height=25),
                                href="https://github.com/OPM/LBPM",
                                target='_blank',
                                style={"margin": "0px 15px 0px 15px"}),

                            html.A(
                                html.Img(src=app.get_asset_url("doc-logo-light.svg"), alt='doc', height=25),
                                href="https://lbpm-sim.org/",
                                target='_blank',
                                style={"margin": "0px 15px 0px 15px"}),
                        ],
                        style={'textAlign': 'right'},
                    )
                ]
            )
            ),
        ], justify="end", align="center", style={"background-color": "#222222", "color": "#EEEEEE"},
        className="py-2 px-3"),

        dbc.Row(
            [
                dbc.Col(
                    [
                        sidebar
                    ], xs=4, sm=4, md=2, lg=2, xl=2, xxl=2),

                dbc.Col(
                    [
                        dash.page_container
                    ], xs=8, sm=8, md=10, lg=10, xl=10, xxl=10)
            ]
        )
    ], fluid=True)

    app.run(debug=True)

    return


if __name__ == "__main__":
    main()
