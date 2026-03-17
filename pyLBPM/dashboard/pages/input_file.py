from pyLBPM.dashboard import ids, layouts, dataloader
from pyLBPM.lbpm_input_database import read_input_database, ExtractDatabaseSection, get_database_section_names
import dash
from dash import html

dash.register_page(__name__, path='/', name="Input Configuration", order=0)  # This will be the landing page

def get_section_string(db):
    db = db.split("\n")
    # input_html = [html.P(line) for line in input_db]
    for b in range(0, len(db)):
        db.insert(b * 2, html.Br())
    return db
    #

sim_dir = dataloader.get_sim_dir()
try:
    input_db = read_input_database(sim_dir / "input.db")
    child = [html.H2("The LBPM simulation was performed with the following input parameters:"),
             html.Br(style={"line-height": 10})]
    sections = get_database_section_names(input_db)
    for section in sections:
        db = ExtractDatabaseSection(input_db, section)
        db = get_section_string(db)
        child.append(html.H4(section, style={"line-height": 10}))
        child.append(html.P(db, style={"margin-left": 40}))
        child.append(html.Hr(style={"line-height": 4}))

    layout = html.Div(
        className="input-config-div",
        children=child#[

            #child,
            # html.H4("Domain:"),
            # html.P(domain_db, style={"margin-left": 40}),
            # html.Hr(),

            # html.P(input_db),
        #]
    )
except FileNotFoundError:
    layout = layouts.create_filenotfound_layout(page_title="Input File")
