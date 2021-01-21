"""Run :mod:`legacysim.runbrick`."""

import os
import sys
import argparse
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

        #if run.brickname != '0589m290': continue
        legacypipe_fn = find_file(base_dir=settings.legacypipe_output_dir,filetype='tractor',source='legacypipe',brickname=run.brickname)

        command = []
        for stage,versions in run.stages.items():
            pythonpath = 'PYTHONPATH=%s' % get_pythonpath(module_dir='/src/',versions=versions,full=True,as_string=True)
            command += [pythonpath]
            command += ['python',runbrick.__file__]
            command += ['--brick',run.brickname,'--threads',threads,'--outdir',settings.output_dir,'--run',settings.run,
                        '--no-wise','--no-write','--stage',stage,
                        '--env-header',legacypipe_fn,'--fileid',4,';']
            #command += ['--brick',run.brickname,'--threads',threads,'--outdir',settings.output_dir,'--run',settings.run,
            #            '--no-wise','--no-write','--stage',stage,
            #            '--env-header',legacypipe_fn,
            #            '--skip','--skip-calibs','--read-serial','--release',9011,'--fileid',3,';']

        output = run_shell(command[:-1])
        print(output)
