from pyLBPM.dashboard import ids, layouts, dataloader
import dash


dash.register_page(__name__, name="SCAL Analysis", order=4)  # This will be the landing page

sim_dir = dataloader.get_sim_dir()

try:
    sim_file = dataloader.csv_reader(simulation_dir=sim_dir, csv_file="SCAL.csv")
    layout = layouts.create_linechart_layout(sim_file, page_title="SCAL Analysis",
                                             plot_id=ids.SCAL_LINE_CHART)

except FileNotFoundError:
    layout = layouts.create_filenotfound_layout(page_title="SCAL Analysis", id_str=ids.SCAL_LINE_CHART)