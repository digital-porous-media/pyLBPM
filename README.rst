# pyLBPM
## A python-based management interface for the LBPM software

## Installation
To install pyLBPM with pip

```
git clone git@github.com:JamesEMcClure/pyLBPM.git
cd pyLBPM
pip install ./
```

To download LBPM dependencies, launch a python command prompt and run the following from the python command line

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
lbpm_config_setup=lbpm_setup.install_dependencies(lbpm_install_path)
```

## Launching simulations

To do: write a python-based launcher for LBPM

## Managing simulation data

To do: add python interface to read CSV data from active or completed simulations

## Visualizing simulation data

To do: write a python interface to read LBPM HDF5 files
