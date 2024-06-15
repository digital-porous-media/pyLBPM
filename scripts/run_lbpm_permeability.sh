#!/bin/bash

# Set the simulation directory
if [-n $1]; then
    SIMULATION_DIRECTORY=$1
else
    SIMULATION_DIRECTORY=`pwd`
fi       
echo "Simulation directory is $SIMULATION_DIRECTORY"
cd $SIMULATION_DIRECTORY

# Check if the number of processors available to LBPM has been set
if [ -n "$LBPM_NUM_PROCS" ]; then
  echo "You supplied the first parameter!"
else
    echo "Set LBPM_NUM_PROCS=1 (default)"
    LBPM_NUM_PROCS=1
fi

echo "LBPM simulation from git commit: $LBPM_GIT_COMMIT"
echo "LBPM install path: $LBPM_BIN"
echo "MPI install path: $MPI_DIR"

LBPM_LAUNCH_COMMAND="$MPIRUN -np $LBPM_NUM_PROCS $LBPM_BIN/lbpm_permeability_simulator"

echo "$LBPM_LAUNCH_COMMAND"

# Launch the simulation and detach from the process
$LBPM_LAUNCH_COMMAND input.db &

exit;
