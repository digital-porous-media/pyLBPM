#!/bin/bash

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

LBPM_LAUNCH_COMMAND="$MPIRUN $LBPM_MPIARGS -np $LBPM_NUM_PROCS $LBPM_BIN/lbpm_color_simulator"

echo "$LBPM_LAUNCH_COMMAND"

$LBPM_LAUNCH_COMMAND input.db
