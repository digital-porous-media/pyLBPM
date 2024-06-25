from pyLBPM.dashboard import ids, layouts, dataloader
import dash

dash.register_page(__name__, name="Pre-Simulation", order=1)  # This will be the landing page

sim_dir = dataloader.get_sim_dir()
try:
    sim_file = dataloader.csv_reader(simulation_dir=sim_dir, csv_file="morphdrain.csv")
    layout = layouts.create_presim_layout(sim_dir, sim_file, page_title="Pre-Simulation",
                                          slice_id=ids.IMAGE_SLICE,
                                          plot_id=ids.MORPHDRAIN_LINE_CHART)
except FileNotFoundError:
    layout = layouts.create_filenotfound_layout(page_title="Pre-Simulation")


