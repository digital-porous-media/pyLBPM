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