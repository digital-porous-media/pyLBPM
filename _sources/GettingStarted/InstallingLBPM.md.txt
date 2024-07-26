## Installing LBPM

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
lbpm_config_setup=lbpm_setup.install_lbpm(lbpm_install_path)