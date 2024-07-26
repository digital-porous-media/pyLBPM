## Managing simulation data

From the command line 
```
python3
```

From the python command line
```
sdir="/path/to/my/simulation"
from pyLBPM import lbpm_color_model
timelog=lbpm_color_model.read_timelog(simulation_directory=sdir, plot_data=False)
print(timelog)
```