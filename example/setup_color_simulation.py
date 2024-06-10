import os
import numpy as np
import urllib.request
from pyLBPM import lbpm_input_database

# Set up the simulation directory
SimulationDir = "/work/02453/mcclurej/ls6/DRP24/Example"
os.chdir(SimulationDir)
print("LBPM color simulation directory path at " + str(SimulationDir))

# Download example data from DRP
urllib.request.urlretrieve("https://www.digitalrocksportal.org/projects/16/images/65566/download/", "lrc32.raw")

# Read the data into python
input_file = "lrc32.raw"
Nz = 512
Ny = 512 
Nx = 512
ID = np.fromfile(input_file,dtype = np.uint8)
ID.shape = (Nz,Ny,Nx)

# Initialize simulation domain from numpy array
domain = lbpm_input_database.domain_db("lrc32",ID)

# run domain decomposition
domain.decomp(2,2,1)

#uncomment this if you want to interactively see a slice of the input file
#z_slice=100
#dm.view(z_slice)

colorSim = lbpm_input_database.color_db(domain)
colorSim.set_protocol('fractional flow')
colorSim.show_config_file()
