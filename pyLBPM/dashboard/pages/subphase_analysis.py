from pyLBPM.dashboard import ids, layouts, dataloader
import dash

dash.register_page(__name__, name="Subphase Analysis", order=3)  # This will be the landing page

sim_dir = dataloader.get_sim_dir()

try:
    sim_file = dataloader.csv_reader(simulation_dir=sim_dir, csv_file="subphase.csv")
    layout = layouts.create_linechart_layout(sim_file, page_title="Subphase Analysis", plot_id=ids.SUBPHASE_LINE_CHART)

except FileNotFoundError:
    layout = layouts.create_filenotfound_layout(page_title="Subphase Analysis", id_str=ids.SUBPHASE_LINE_CHART)