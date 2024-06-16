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
                    
    def save_config_file(self):
        LBPM_input_file = "Domain {\n"
        LBPM_input_file += '   Filename = "'+str(self.Dm.name)+'"'+"\n"
        LBPM_input_file += '   ReadType ="8bit"'+"\n"
        LBPM_input_file += '   voxel_length = '+str(self.Dm.voxel_length)+"\n"
        LBPM_input_file += "   N = "+str(self.Dm.Nx)+", "+str(self.Dm.Ny)+", "+str(self.Dm.Nz)+"\n"
        LBPM_input_file += "   offset = " + lbpm_input_string_from_list(self.Dm.region[0:3]) +"\n"
        LBPM_input_file += "   nproc = " + lbpm_input_string_from_list(self.Dm.nproc) +"\n"
        LBPM_input_file += "   n = "+str(self.Dm.nx)+", "+str(self.Dm.ny)+", "+str(self.Dm.nz)+"\n"
        LBPM_input_file += "   ReadValues = " + lbpm_input_string_from_list(self.Dm.labels) +"\n"
        LBPM_input_file += "   WriteValues = " + lbpm_input_string_from_list(self.Dm.write_labels) +"\n"
        LBPM_input_file += "   ComponentLabels = " + lbpm_input_string_from_list(self.Dm.solid_labels) +"\n"
        LBPM_input_file += "   BC = "+str(self.Dm.BoundaryCondition)+"\n"
        LBPM_input_file += '}\n'
        LBPM_input_file += "MRT {\n"            
        LBPM_input_file += '   timestepMax = '+str(self.timestepMax)+"\n"
        LBPM_input_file += '   tau = '+str(self.tau)+"\n"
        LBPM_input_file += "   F = " + lbpm_input_string_from_list(self.F) +"\n"
        LBPM_input_file += "   outletLayers = " + lbpm_input_string_from_list(self.outletLayers) +"\n"
        LBPM_input_file += "   inletLayers = " + lbpm_input_string_from_list(self.inletLayers) +"\n"
        LBPM_input_file += '}\n'
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

