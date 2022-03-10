#!/bin/bash
# Set up the legacypipe environment

# add here legacysim to python path if necessary
#export PYTHONPATH=$HOME/legacysim/py:$PYTHONPATH

# set number of OpenMP threads here
export OMP_NUM_THREADS=10
source ./legacypipe-env.sh
#chmod u+x ./runbrick.sh

python mpi_main_runbricks.py "$@"
