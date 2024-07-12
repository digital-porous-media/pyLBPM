import os
import sys
import numpy as np
import urllib.request
from pyLBPM import lbpm_domain
from pyLBPM import lbpm_color_model
from pyLBPM import lbpm_morphology

# LBPM simulation environment variables -- these need to be set from config file
print(os.environ['LBPM_GIT_COMMIT'])
#print(os.environ['LBPM_BIN'])
#print(os.environ['MPI_DIR'])
#print(os.environ['LBPM_MPIARGS'])

# Set up the simulation directory
# get the simulation directory as argument
try:
    SimulationDir=sys.argv[1]
    print(SimulationDir)
    os.chdir(SimulationDir)
    print("LBPM color simulation directory path at " + str(SimulationDir))
except:
    print('ERROR: must provide simulation directory as argument:')
    print('example usage: python setup_color_simulation.py /path/to/simulation/directory ')

# Download example data from DRP
print("Downloading example data from digitalrocksportal.org...")
INPUT_FILE="lrc32.raw"
DRP_LINK="https://www.digitalrocksportal.org/projects/16/images/65566/download/"
urllib.request.urlretrieve(DRP_LINK, INPUT_FILE)
print("   Done.")
      
# Read the data into python
print("Setting up the domain structure...")
Nz = 512
Ny = 512 
Nx = 512
ID = np.fromfile(INPUT_FILE,dtype = np.uint8)
ID.shape = (Nz,Ny,Nx)

# Initialize simulation domain from numpy array
domain = lbpm_domain.domain_db(INPUT_FILE,ID)

# select subregion and domain decomposition
domain.relabel([1, 0])
domain.subregion([0,0,0],[256,256,256])
domain.decomp([1,1,1])
print("    Done.")

#uncomment this if you want to interactively see a slice of the input file
#z_slice=100
#dm.view(z_slice)

print("Run morphological analysis")
morphDrain = lbpm_morphology.morph_db(domain)
morphDrain.target_saturation = 0.25
morphDrain.save_config_file()
lbpm_morphology.run_drainage(SimulationDir)
print("    Done.")

print("Read in the morphological file")
MORPH_FILE=INPUT_FILE+".morphdrain.raw"
# get the updated domain size
Nx = domain.region[3]
Ny = domain.region[4]
Nz = domain.region[5]
# read the image
ID = np.fromfile(MORPH_FILE,dtype = np.uint8)
ID.shape = (Nz,Ny,Nx)
# update the domain
domain = lbpm_domain.domain_db(MORPH_FILE,ID)
domain.decomp([1,1,1])

print("Saving input file...")
colorSim = lbpm_color_model.color_db(domain)
colorSim.set_protocol('fractional flow')

# manually edit the configuration
# (use less timesteps so it finishes quickly_
colorSim.timestepMax=5000
colorSim.save_config_file()
print("    Done.")
print("Setup complete")
