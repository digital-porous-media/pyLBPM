from pyLBPM.dashboard import ids, layouts, dataloader
from pyLBPM.lbpm_input_database import read_input_database
import dash
from dash import html

dash.register_page(__name__, path='/', name="Input Configuration", order=0)  # This will be the landing page

sim_dir = dataloader.get_sim_dir()
try:
    input_db = read_input_database(sim_dir / "input.db")
    input_db = input_db.split("\n")
    # input_html = [html.P(line) for line in input_db]
    for b in range(0, len(input_db)):
        input_db.insert(b * 2, html.Br())
    # input_db = input_db.replace("\n", "<br />")
    # print(type(input_db))
    layout = html.Div(
        className="input-config-div",
        children=[
            html.H1("Simulation Input Configuration"),
            html.Hr(),
            html.P(input_db),
        ]
    )
except FileNotFoundError:
    layout = layouts.create_filenotfound_layout(page_title="Input File")
