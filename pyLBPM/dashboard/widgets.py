from dash import html, dcc


def render_dropdown(all_categories: list[str], id_str: str,
                    heading: str = "", multi_selection: bool = True, default_column_id: int = 0) -> html.Div:
    # all_categories: list[str] = data.keys().tolist()

    return html.Div(
        children=[
            html.H6(heading),
            dcc.Dropdown(
                multi=multi_selection,
                id=id_str,
                options=[{"label": i, "value": i} for i in all_categories],
                value=all_categories[default_column_id],
                persistence=False
            ),
        ]
    )


def render_slider(timesteps: list[int], id_str: str, heading: str = "") -> html.Div:
    mark_vals = {key: value for key, value in zip(range(len(timesteps)), timesteps)}

    return html.Div(
        children=[
            html.H6(heading),
            dcc.Slider(
                id=id_str,
                min=0,
                max=len(timesteps)-1,
                step=1,
                value=0,
                marks=mark_vals,
            ),
        ]
    )
