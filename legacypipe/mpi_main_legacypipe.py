"""Run :mod:`legacypipe.runbrick`."""

import os
import sys
import argparse
from legacysim import RunCatalog,find_file
from legacysim.batch import TaskManager,run_shell,EnvironmentManager,get_pythonpath

ntasks = int(os.getenv('SLURM_NTASKS','1'))
threads = int(os.getenv('OMP_NUM_THREADS','1'))

parser = argparse.ArgumentParser(description='Legacypipe main runbrick')
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
            environment = EnvironmentManager(fn=legacypipe_fn)
            command = ['%s=%s' % (key,val) for key,val in environment.environ.items()]
            pythonpath = get_pythonpath(module_dir='/src/',versions=versions,full=True,as_string=False)
            command += ['PYTHONPATH=%s' % ':'.join(pythonpath)]
            command += ['python',os.path.join(pythonpath[0],'legacypipe','runbrick.py')]
            command += ['--brick',run.brickname,'--threads',threads,'--outdir',settings.output_dir,'--run',settings.run,
                        '--no-wise','--no-write','--stage',stage,';']
            #command += ['--brick',run.brickname,'--threads',threads,'--outdir',settings.output_dir,'--run',settings.run,
            #            '--no-wise','--no-write','--stage',stage,'--skip','--skip-calibs',';']

        output = run_shell(command[:-1])
        print(output)
