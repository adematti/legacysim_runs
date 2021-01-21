import os

survey_dir = os.getenv('LEGACY_SURVEY_DIR')
run = 'north'
output_dir = os.path.join(os.getenv('CSCRATCH'),'legacysim','dr9','legacypipe',run)
randoms_input_fn = '/global/cfs/cdirs/cosmo/data/legacysurvey/dr9/randoms/randoms-1-0.fits'
bricklist_fn = 'bricklist_%s.txt' % run
runlist_fn = 'runlist_%s.txt' % run

def get_bricknames():
    return [brickname[:-len('\n')] for brickname in open(bricklist_fn,'r')]

legacypipe_output_dir = os.path.join(os.getenv('LEGACYPIPE_SURVEY_DIR'),run)
