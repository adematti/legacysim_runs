legacypipe
==========

Run a few bricks to check **legacysim** against **legacypipe** in north and south.

On NERSC
--------

Set up data::

  mkdir -p ${CSCRATCH}/legacysim/dr9/data/
  cp /global/cfs/cdirs/cosmo/data/legacysurvey/dr9/ccds-annotated-* ${CSCRATCH}/legacysim/dr9/data/
  cp /global/cfs/cdirs/cosmo/data/legacysurvey/dr9/survey-* ${CSCRATCH}/legacysim/dr9/data/
  ln -s /global/cfs/cdirs/cosmo/data/legacysurvey/dr9/calib/ ${CSCRATCH}/legacysim/dr9/data/
  ln -s /global/cfs/cdirs/cosmo/work/legacysurvey/dr9m/images/ ${CSCRATCH}/legacysim/dr9/data/

Pull Docker image::

  shifterimg -v pull adematti/legacysim:DR9

Then create run lists::

  shifter --volume ${HOME}:/homedir/ --image=adematti/legacysim:DR9 python /src/legacysim/py/legacysim/scripts/runlist.py --outdir /global/cfs/cdirs/cosmo/data/legacysurvey/dr9/north --brick bricklist_north.txt --write-list runlist_north.txt --modules docker
  shifter --volume ${HOME}:/homedir/ --image=adematti/legacysim:DR9 python /src/legacysim/py/legacysim/scripts/runlist.py --outdir /global/cfs/cdirs/cosmo/data/legacysurvey/dr9/south --brick bricklist_south.txt --write-list runlist_south.txt --modules docker

Run::

  chmod u+x ./mpi_runbricks.sh
  salloc -N 1 -C haswell -t 02:00:00 --qos interactive -L SCRATCH,project
  srun -n 5 shifter --module=mpich-cle6 --volume ${HOME}:/homedir/ --image=adematti/legacysim:DR9 ./mpi_runbricks.sh --run north

and similarly for south::

  salloc -N 1 -C haswell -t 02:00:00 --qos interactive -L SCRATCH,project
  srun -n 5 shifter --module=mpich-cle6 --volume ${HOME}:/homedir/ --image=adematti/legacysim:DR9 ./mpi_runbricks.sh --run south

.. note::

  With 5 tasks ``srun -n 4``, there will be 1 root and 4 workers, hence 4 bricks run in parallel.

Check everything ran::

  shifter --volume ${HOME}:/homedir/ --image=adematti/legacysim:DR9 python /src/legacysim/py/legacysim/scripts/check.py --outdir $CSCRATCH/legacysim/dr9/legacypipe/north --brick runlist_north.txt
  shifter --volume ${HOME}:/homedir/ --image=adematti/legacysim:DR9 python /src/legacysim/py/legacysim/scripts/check.py --outdir $CSCRATCH/legacysim/dr9/legacypipe/south --brick runlist_south.txt
