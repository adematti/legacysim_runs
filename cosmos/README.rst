Cosmos
======

Run 1000 bricks covering a large EBV range in south and south.

On NERSC
--------

Set up data::

  mkdir -p ${CSCRATCH}/legacysim/dr9/data/
  cp /global/cfs/cdirs/cosmo/data/legacysurvey/dr9/ccds-annotated-* ${CSCRATCH}/legacysim/dr9/data/
  cp /global/cfs/cdirs/cosmo/data/legacysurvey/dr9/survey-* ${CSCRATCH}/legacysim/dr9/data/
  ln -s /global/cfs/cdirs/cosmo/data/legacysurvey/dr9/calib/ ${CSCRATCH}/legacysim/dr9/data/
  ln -s /global/cfs/cdirs/cosmo/work/legacysurvey/dr9/images/ ${CSCRATCH}/legacysim/dr9/data/

Pull Docker image::

  shifterimg -v pull adematti/legacysim:DR9

Set up catalogs of sources to be injected::

  source legacypipe-env.sh
  shifter --volume ${HOME}:/homedir/ --image=adematti/legacysim:DR9 python preprocess.py --do injected --run south

Then create run lists::

  shifter --volume ${HOME}:/homedir/ --image=adematti/legacysim:DR9 python /src/legacysim/py/legacysim/scripts/runlist.py --outdir /global/cfs/cdirs/cosmo/data/legacysurvey/dr9/south --brick bricklist_south.txt --write-list runlist_south.txt --modules docker

Run::

  chmod u+x ./mpi_runbricks.sh
  salloc -N 2 -C haswell -t 01:30:00 --qos interactive -L SCRATCH,project
  srun -n 11 shifter --module=mpich-cle6 --volume ${HOME}:/homedir/ --image=adematti/legacysim:DR9 ./mpi_runbricks.sh --run south

.. note::

  With 101 tasks ``srun -n 101``, there will be 1 root and 100 workers, hence 100 bricks run in parallel.

Check everything ran and match::

  shifter --volume ${HOME}:/homedir/ --image=adematti/legacysim:DR9 /bin/bash
  python /src/legacysim/py/legacysim/scripts/check.py --outdir ${CSCRATCH}/legacysim/dr9/cosmos/south --list runlist_400N-EBV.txt
  python /src/legacysim/py/legacysim/scripts/match.py --cat-dir ${CSCRATCH}/legacysim/dr9/cosmos/south/file0_rs0_skip0/merged --outdir ${CSCRATCH}/legacysim/dr9/cosmos/south --plot-hist plots/hist_south.png
  exit

and similarly for south. Other commands::

  python /src/legacysim/py/legacysim/scripts/merge.py --filetype injected --cat-dir $CSCRATCH/legacysim/dr9/cosmos/south/file0_rs0_skip0/merged --outdir $CSCRATCH/legacysim/dr9/cosmos/south
  python /src/legacysim/py/legacysim/scripts/merge.py --filetype tractor --cat-dir $CSCRATCH/legacysim/dr9/cosmos/south/file0_rs0_skip0/merged --outdir $CSCRATCH/legacysim/dr9/cosmos/south
  python /src/legacysim/py/legacysim/scripts/match.py --tractor-legacypipe /global/cfs/cdirs/cosmo/data/legacysurvey/dr9/south/ --outdir $CSCRATCH/legacysim/dr9/cosmos/south --cat-fn $CSCRATCH/legacysim/dr9/cosmos/south/file0_rs0_skip0/merged/matched_legacypipe_input.fits
  python /src/legacysim/py/legacysim/scripts/cutout.py --outdir $CSCRATCH/legacysim/dr9/cosmos/south --plot-fn "plots/cutout_south-%(brickname)s-%(icut)d.png" --ncuts 2
  python /src/legacysim/py/legacysim/scripts/resources.py --outdir $CSCRATCH/legacysim/dr9/cosmos/south --plot-fn plots/resources-summary_south.png
