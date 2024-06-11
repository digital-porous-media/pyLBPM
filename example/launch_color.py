import os
import numpy as np
import urllib.request
from pyLBPM import lbpm_domain
from pyLBPM import lbpm_color_model

print("Running LBPM built from git commit " + str(os.environ['LBPM_GIT_COMMIT']))

# Set up the simulation directory
SimulationDir = "/work/02453/mcclurej/ls6/DRP24/Example"
os.chdir(SimulationDir)
print("Simulation directory is " + SimulationDir)

lbpm_color_model.launch_simulation()
