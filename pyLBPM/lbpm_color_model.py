import re
import os
import subprocess
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pyLBPM.lbpm_input_database	import *

class FlowAdaptor_db:
    def __init__(self):
        self.max_steady_timesteps = 200000
        self.min_steady_timesteps = 100000
        self.fractional_flow_increment = 0.1
        self.mass_fraction_factor = 0.0002
        self.endpoint_threshold = 0.1

    def add_section(self,LBPM_input_file):
        LBPM_input_file += "FlowAdaptor {\n"
        LBPM_input_file += '   max_steady_timesteps = '+str(self.max_steady_timesteps)+"\n"
        LBPM_input_file += '   min_steady_timesteps = '+str(self.min_steady_timesteps)+"\n"
        LBPM_input_file += '   fractional_flow_increment = '+str(self.fractional_flow_increment)+"\n"
        LBPM_input_file += '   mass_fraction_factor = '+str(self.mass_fraction_factor)+"\n"
        LBPM_input_file += '   endpoint_threshold = '+str(self.endpoint_threshold)+"\n"
        LBPM_input_file += "}\n"
        return(LBPM_input_file)

class Analysis_db:
    def __init__(self):
        self.subphase_analysis_interval = 5000
        self.analysis_interval = 1000
        
    def add_section(self,LBPM_input_file):
        LBPM_input_file += 'Analysis { \n'
        LBPM_input_file += '   restart_file = "Restart"\n'
        LBPM_input_file += '   analysis_interval = '+str(self.analysis_interval)+"\n"
        LBPM_input_file += '   subphase_analysis_interval = '+str(self.subphase_analysis_interval)+"\n"
        LBPM_input_file += '}\n'
        return(LBPM_input_file)

class Visualization_db:
    def __init__(self):
        self.save_8bit_raw = True
        self.write_silo = False
        
    def add_section(self,LBPM_input_file):
        LBPM_input_file += 'Visualization { \n'
        LBPM_input_file += '   save_8bit_raw = true \n'
        LBPM_input_file += '   write_silo = false \n'
        LBPM_input_file += '}\n'
        return(LBPM_input_file)
    
class color_db:

    def __init__(self, domain):
        # Domain should be initialized from 3D numpy array
        # set up default values for input parameters
        self.Dm = domain
        self.FlowAdaptor = FlowAdaptor_db()
        self.Visualization = Visualization_db()
        self.Analysis = Analysis_db()
        
        self.protocols = [ 'fractional flow',
                          'centrifuge', 
                          'core flooding', 
                          'image sequence'
                         ]
        self.protocol = "user specified"
        self.restart = False
        self.BC = self.Dm.BoundaryCondition
        self.useProtocol = False
        self.timestepMax = 10000000
        self.tauA = 0.7
        self.tauB = 0.7
        self.rhoA = 1.0
        self.rhoB = 1.0
        self.alpha = 0.01
        self.beta = 0.95
        self.F = [0.0, 0.0, 0.0]
        self.outletLayers = [0, 0, 5]
        self.inletLayers = [0, 0, 5]
        self.flux = 0.0
        self.capillary_number = 1.0e-5
        self.wetting_values = []
        for i in domain.solid_labels:
            self.wetting_values.append(1.0)
            
        print("Solid labels from domain: "
              + str(self.Dm.solid_labels)
             )
        print("Default wetting labels:   "
              + str(self.wetting_values)
              + " (change manually if desired)"
             )
    def set_protocol(self, string):
        self.useProtocol = False
        for option in self.protocols:
            if (option == string):
                self.protocol = option
                self.useProtocol = True
                print("Protocol selected: " + option)
                
                if (self.protocol == "fractional flow"):
                    self.F =  [0.0, 0.0, 1.0e-5]
                    self.outletLayers = [0, 0, 5]
                    self.inletLayers = [0, 0, 5]
                    self.target_capillary = 1.0e-5
                    self.Dm.BoundaryCondition = 0
                    
                elif (self.protocol == "core flooding"):
                    self.Dm.BoundaryCondition = 4
                    #self.flux = capillary_number*interfacial_tension/(rho_w*nu_w)
                    print("not implemented")
                    
            self.BC = self.Dm.BoundaryCondition

                    
        if (self.useProtocol == False):
            print("Protocol not set. Please choose from the options below\n" 
                  + str(self.protocols))

    def add_section(self,LBPM_input_file):
        LBPM_input_file += "Color {\n"
        if (self.useProtocol):
            LBPM_input_file += '   protocol = "'+str(self.protocol)+'"'+"\n"
        LBPM_input_file += '   Restart = '+str(self.restart)+"\n"
        LBPM_input_file += '   WettingConvention = "SCAL"'+"\n"
        LBPM_input_file += "   ComponentLabels = " + lbpm_input_string_from_list(self.Dm.solid_labels) +"\n"
        LBPM_input_file += "   ComponentAffinity = " + lbpm_input_string_from_list(self.wetting_values) +"\n"
        LBPM_input_file += '   timestepMax = '+str(self.timestepMax)+"\n"
        LBPM_input_file += '   tauA = '+str(self.tauA)+"\n"
        LBPM_input_file += '   tauB = '+str(self.tauB)+"\n"
        LBPM_input_file += '   rhoA = '+str(self.rhoA)+"\n"
        LBPM_input_file += '   rhoB = '+str(self.rhoB)+"\n"
        LBPM_input_file += '   alpha = '+str(self.alpha)+"\n"
        LBPM_input_file += '   beta = '+str(self.beta)+"\n"
        LBPM_input_file += '   capillary_number = '+str(self.capillary_number)+"\n"
        LBPM_input_file += "   F = " + lbpm_input_string_from_list(self.F) +"\n"
        LBPM_input_file += "   outletLayers = " + lbpm_input_string_from_list(self.outletLayers) +"\n"
        LBPM_input_file += "   inletLayers = " + lbpm_input_string_from_list(self.inletLayers) +"\n"
        LBPM_input_file += '}\n'
        return(LBPM_input_file)

    def save_config_file(self):
        LBPM_input_file=self.Dm.add_section("")
        LBPM_input_file=self.add_section(LBPM_input_file)
        LBPM_input_file=self.Visualization.add_section(LBPM_input_file)
        LBPM_input_file=self.Analysis.add_section(LBPM_input_file) 
        LBPM_input_file=self.FlowAdaptor.add_section(LBPM_input_file)
        create_input_database("input.db",LBPM_input_file)
        print(LBPM_input_file)        

def launch_simulation(simulation_directory):
    success=subprocess.run(["bash", "run_lbpm_color.sh", simulation_directory])

def read_timelog(simulation_directory, plot_data=True):
    DATA=pd.read_csv(str(simulation_directory+"/timelog.csv"),sep=" ")

    if (plot_data):
        plt.figure()
        plt.plot(DATA['sw'])
        plt.xlabel('time increment')
        plt.ylabel('saturation')
        plt.show()
        
    return DATA

def read_subphase(simulation_directory, plot_data=True):
    DATA=pd.read_csv(str(simulation_directory+"/subphase.csv"),sep=" ")

    if (plot_data):
        plt.figure()
        plt.plot(DATA['time'],DATA['Vwc'])
        plt.xlabel('timestep')
        plt.ylabel('connected water volume')
        plt.show()
        
    return DATA

def read_scal(simulation_directory, plot_data=True, permeability=1.0):
    SCAL=pd.read_csv(str(simulation_directory+"/SCAL.csv"),sep=" ")

    # Scale the curve to the permeability (if provided)
    krn=SCAL['eff.perm.oil.upper.bound']/permeability
    krw=SCAL['eff.perm.water.upper.bound']/permeability

    if (plot_data):
        plt.figure()
        plt.plot(SCAL['sat.water'],krn, c='r', label='oil')
        plt.plot(SCAL['sat.water'],krw, c='b', label='water')
        plt.xlabel('water saturation')
        plt.ylabel('relative permeability')
        ax = plt.gca()
        ax.set_xlim([0,1])
        plt.legend()
        plt.show()
    
    return SCAL

