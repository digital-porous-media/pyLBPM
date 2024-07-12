import os
import sys
import numpy as np
import urllib.request
from pyLBPM import lbpm_domain
from pyLBPM import lbpm_permeability_model

print("Running LBPM built from git commit " + str(os.environ['LBPM_GIT_COMMIT']))

# Set up the simulation directory
try:
    SimulationDir=sys.argv[1]
    print(SimulationDir)
    os.chdir(SimulationDir)
    print("LBPM permeability simulation directory path at " + str(SimulationDir))
except:
    print('Please provide simulation directory as argument:')
    print('example usage: python setup_color_simulation.py /path/to/simulation/directory ')

#os.chdir(SimulationDir)
print("Simulation directory is " + SimulationDir)

lbpm_permeability_model.launch_simulation(SimulationDir)
