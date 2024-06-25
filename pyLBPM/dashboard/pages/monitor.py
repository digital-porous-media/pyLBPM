from pyLBPM.dashboard import ids, layouts, dataloader
import dash


dash.register_page(__name__,  name="Monitor Simulations", order=2)

sim_dir = dataloader.get_sim_dir()
# sim_dir = "/Users/bchang/Documents/porescale_quantification_workshop/lbpm/lrc32_Ca1e-4"
#r"C:\Users\bchan\Documents\porescale_quantification_workshop\lbpm\lrc32_Ca1e-4"
try:
    sim_file = dataloader.csv_reader(simulation_dir=sim_dir, csv_file="timelog.csv")

    layout = layouts.create_linechart_layout(sim_file, page_title="Timelog Monitoring", class_name="timelog-div",
                                             plot_id=ids.TIMELOG_LINE_CHART)
except FileNotFoundError:
    layout = layouts.create_filenotfound_layout(page_title="Timelog Monitoring", class_name="timelog-div",
                                                id_str=ids.TIMELOG_LINE_CHART)