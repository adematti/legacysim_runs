"""Run :mod:`legacysim.runbrick`."""

import os
import argparse
import time
from legacysim import RunCatalog,find_file,runbrick
from legacysim.batch import TaskManager,run_shell,get_pythonpath

ntasks = int(os.getenv('SLURM_NTASKS','1'))
threads = int(os.getenv('OMP_NUM_THREADS','1'))

parser = argparse.ArgumentParser(description='legacysim main runbrick')
parser.add_argument('-r','--run',type=str,choices=['north','south'],required=True,help='Run?')
opt = parser.parse_args()

if opt.run == 'north':
    import settings_north as settings
else:
    import settings_south as settings

runcat = RunCatalog.from_list(settings.runlist_fn)

with TaskManager(ntasks=ntasks) as tm:

    for run in tm.iterate(runcat):

        legacypipe_fn = find_file(base_dir=settings.legacypipe_output_dir,filetype='tractor',source='legacypipe',brickname=run.brickname)

        command = []
        for stage,versions in run.stages.items():
            pythonpath = 'PYTHONPATH=%s' % get_pythonpath(module_dir='/src/',versions=versions,full=True,as_string=True)
            command += [pythonpath]
            command += ['python',runbrick.__file__]
            command += ['--brick',run.brickname,'--threads',threads,'--outdir',settings.output_dir,'--run',settings.run,
                        '--injected-fn',settings.injected_fn,'--fileid',run.fileid,'--rowstart',run.rowstart,'--skipid',run.skipid,
                        '--sim-blobs','--sim-stamp','tractor','--add-sim-noise','poisson','--no-wise',
                        '--skip-calibs','--write-stage',stage,'--write-log','--ps','--ps-t0',int(time.time()),'--stage',stage,
                        '--env-header',legacypipe_fn,';']

        #print(command)
        output = run_shell(command[:-1])
        print(output)
