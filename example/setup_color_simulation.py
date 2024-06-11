import os
import numpy as np
import urllib.request
from pyLBPM import lbpm_domain
from pyLBPM import lbpm_color_model

# LBPM simulation environment variables -- these need to be set from config file
print(os.environ['LBPM_GIT_COMMIT'])
#print(os.environ['LBPM_BIN'])
#print(os.environ['MPI_DIR'])
#print(os.environ['LBPM_MPIARGS'])

# Set up the simulation directory
SimulationDir = "/work/02453/mcclurej/ls6/DRP24/Example"
os.chdir(SimulationDir)
print("LBPM color simulation directory path at " + str(SimulationDir))

# Download example data from DRP
INPUT_FILE="lrc32.raw"
DRP_LINK="https://www.digitalrocksportal.org/projects/16/images/65566/download/"
urllib.request.urlretrieve(DRP_LINK, INPUT_FILE)

# Read the data into python
Nz = 512
Ny = 512 
Nx = 512
ID = np.fromfile(INPUT_FILE,dtype = np.uint8)
ID.shape = (Nz,Ny,Nx)

# Initialize simulation domain from numpy array
domain = lbpm_domain.domain_db(INPUT_FILE,ID)

# select subregion and domain decomposition
domain.subregion([0,0,0],[256,256,256])
domain.decomp([1,1,1])

#uncomment this if you want to interactively see a slice of the input file
#z_slice=100
#dm.view(z_slice)

colorSim = lbpm_color_model.color_db(domain)
colorSim.set_protocol('fractional flow')
colorSim.show_config_file()


