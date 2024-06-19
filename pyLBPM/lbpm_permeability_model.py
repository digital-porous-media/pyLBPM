import re
import os
import subprocess
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pyLBPM.lbpm_input_database import *

class permeability_db:

    def __init__(self, domain):
        # Domain should be initialized from 3D numpy array
        # set up default values for input parameters
        self.Dm = domain
        self.timestepMax = 100000
        self.tau = 0.7
        self.F = [0.0, 0.0, 1.0e-5]
        self.outletLayers = [0, 0, 5]
        self.inletLayers = [0, 0, 5]
        self.flux = 0.0

    def add_section(self,LBPM_input_file):
        LBPM_input_file += "MRT {\n"            
        LBPM_input_file += '   timestepMax = '+str(self.timestepMax)+"\n"
        LBPM_input_file += '   tau = '+str(self.tau)+"\n"
        LBPM_input_file += "   F = " + lbpm_input_string_from_list(self.F) +"\n"
        LBPM_input_file += "   outletLayers = " + lbpm_input_string_from_list(self.outletLayers) +"\n"
        LBPM_input_file += "   inletLayers = " + lbpm_input_string_from_list(self.inletLayers) +"\n"
        LBPM_input_file += '}\n'
        return(LBPM_input_file)    

    def save_config_file(self):
        LBPM_input_file=self.Dm.add_section("")
        LBPM_input_file=self.add_section(LBPM_input_file)
        LBPM_input_file += 'Visualization { \n'
        LBPM_input_file += '   save_8bit_raw = false \n'
        LBPM_input_file += '   write_silo = false \n'
        LBPM_input_file += '}\n'
        create_input_database("input.db",LBPM_input_file)
        print(LBPM_input_file)

def launch_simulation(simulation_directory):
    success=subprocess.run(["bash", "run_lbpm_permeability.sh", simulation_directory])

def read_timelog(simulation_directory, plot_data=True):
    DATA=pd.read_csv(str(simdir+"/timelog.csv"),sep=" ")

    if (plot_data):
        plt.figure()
        plt.plot(DATA['sw'])
        plt.xlabel('time increment')
        plt.ylabel('saturation')
        plt.show()
        
    return DATA

