# pyLBPM

## A python-based management interface for the LBPM software

## Installation
To install pyLBPM with pip (note Python installs scripts to `$HOME/.local/.bin`)

```
git clone git@github.com:digital-porous-media/pyLBPM.git
cd pyLBPM
pip install ./
export PATH=$HOME/.local/bin:$PATH
```

⚠️ Note
It is best to run the following lines from nodes with access to a GPU. On Texas Advanced Computing Center (TACC) systems, this can be done using an interactive development session. The total installation time takes 1-2 hours.
<details>
<summary>Accessing idev on TACC Vista</summary>

```bash
idev -p gh-dev -t 2:00:00
module load gcc cuda python3
```
</details> 

<details> 
<summary>Accessing idev on TACC Lonestar6</summary>
 
```bash
idev -p gpu-a100-small -t 2:00:00
module load gcc/9.4.0 cuda
```
</details>

To download LBPM dependencies, launch a Python command prompt and run the following from the Python command line.

```
from pyLBPM import lbpm_setup
lbpm_install_path="~/local"
lbpm_config_setup=lbpm_setup.download_dependencies(lbpm_install_path)
lbpm_config_setup=lbpm_setup.install_dependencies(lbpm_install_path)

```


To install LBPM from the python command line
```
from pyLBPM import lbpm_setup
lbpm_install_path="~/local"
lbpm_config_setup=lbpm_setup.install_lbpm(lbpm_install_path)
```

## Launching simulations
Step 1. Set up a working directory for your simulation
```
SIMDIR=/path/to/my/simulation
mkdir -p $SIMDIR
```
Step 2. Run example scripts to setup a simple simulation (modify as needed to suit your case)
```
 python example/setup_color_simulation.py $SIMDIR
```
Step 3.
Launch the simulation (should capture local build environment from config files)
```
python example/launch_color.py $SIMDIR
```

## Managing simulation data

From the python command line
```
sdir="/path/to/my/simulation"
from pyLBPM import lbpm_color_model
timelog=lbpm_color_model.read_timelog(simulation_directory=sdir, plot_data=False)
print(timelog)
```


## Visualizing simulation data

To do: write a python interface to read LBPM HDF5 files
