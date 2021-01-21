EBV 1000
========

Run 1000 bricks covering a large EBV range in north and south.

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

Set up catalogs of sources to be injected::

  source legacypipe-env.sh
  shifter --volume ${HOME}:/homedir/ --image=adematti/legacysim:DR9 python preprocess.py --do injected --run north

and similarly (``--run south``) for south. Then create run lists::

  shifter --volume ${HOME}:/homedir/ --image=adematti/legacysim:DR9 python /src/legacysim/py/legacysim/scripts/runlist.py --outdir /global/cfs/cdirs/cosmo/data/legacysurvey/dr9/north --brick bricklist_400N-EBV.txt --write-list runlist_400N-EBV.txt --modules docker
  shifter --volume ${HOME}:/homedir/ --image=adematti/legacysim:DR9 python /src/legacysim/py/legacysim/scripts/runlist.py --outdir /global/cfs/cdirs/cosmo/data/legacysurvey/dr9/south --brick bricklist_600S-EBV.txt --write-list runlist_600S-EBV.txt --modules docker

Run::

  chmod u+x ./mpi_runbricks.sh
  salloc -N 20 -C haswell -t 03:00:00 --qos interactive -L SCRATCH,project
  srun -n 101 shifter --module=mpich-cle6 --volume ${HOME}:/homedir/ --image=adematti/legacysim:DR9 ./mpi_runbricks.sh --run north

and similarly for south::

  salloc -N 30 -C haswell -t 03:00:00 --qos interactive -L SCRATCH,project
  srun -n 151 shifter --module=mpich-cle6 --volume ${HOME}:/homedir/ --image=adematti/legacysim:DR9 ./mpi_runbricks.sh --run south

.. note::

  With 101 tasks ``srun -n 101``, there will be 1 root and 100 workers, hence 100 bricks run in parallel.

Check everything ran and match::

  shifter --volume ${HOME}:/homedir/ --image=adematti/legacysim:DR9 /bin/bash
  python /src/legacysim/py/legacysim/scripts/check.py --outdir $CSCRATCH/legacysim/dr9/ebv1000shaper/north --list runlist_400N-EBV.txt
  python /src/legacysim/py/legacysim/scripts/match.py --cat-dir $CSCRATCH/legacysim/dr9/ebv1000shaper/north/file0_rs0_skip0/merged --outdir $CSCRATCH/legacysim/dr9/ebv1000shaper/north --plot-hist plots/hist_north.png
  exit

and similarly for south. Other commands::

  python /src/legacysim/py/legacysim/scripts/merge.py --filetype injected --cat-dir $CSCRATCH/legacysim/dr9/ebv1000shaper/north/file0_rs0_skip0/merged --outdir $CSCRATCH/legacysim/dr9/ebv1000shaper/north
  python /src/legacysim/py/legacysim/scripts/merge.py --filetype tractor --cat-dir $CSCRATCH/legacysim/dr9/ebv1000shaper/north/file0_rs0_skip0/merged --outdir $CSCRATCH/legacysim/dr9/ebv1000shaper/north
  python /src/legacysim/py/legacysim/scripts/match.py --tractor-legacypipe /global/cfs/cdirs/cosmo/data/legacysurvey/dr9/north/ --outdir $CSCRATCH/legacysim/dr9/ebv1000shaper/north --cat-fn $CSCRATCH/legacysim/dr9/ebv1000shaper/north/file0_rs0_skip0/merged/matched_legacypipe_input.fits
  python /src/legacysim/py/legacysim/scripts/cutout.py --outdir $CSCRATCH/legacysim/dr9/ebv1000shaper/north --plot-fn "plots/cutout_north-%(brickname)s-%(icut)d.png" --ncuts 2
  python /src/legacysim/py/legacysim/scripts/resources.py --outdir $CSCRATCH/legacysim/dr9/ebv1000shaper/north --plot-fn plots/resources-summary_north.png
