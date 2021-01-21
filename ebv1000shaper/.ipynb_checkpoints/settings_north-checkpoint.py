import os

survey_dir = os.getenv('LEGACY_SURVEY_DIR')
run = 'north'
output_dir = os.path.join(os.getenv('CSCRATCH'),'legacysim','dr9','ebv1000shaper',run)
randoms_fn = '/global/cfs/cdirs/cosmo/data/legacysurvey/dr9/randoms/randoms-1-0.fits'
truth_fn = '/project/projectdirs/desi/users/ajross/MCdata/seed.fits'
injected_fn = os.path.join(output_dir,'injected','injected.fits')
bricklist_fn = 'bricklist_400N-EBV.txt'
runlist_fn = 'runlist_400N-EBV.txt'

def get_bricknames():
    return [brickname[:-len('\n')] for brickname in open(bricklist_fn,'r')]

legacypipe_output_dir = os.path.join(os.getenv('LEGACYPIPE_SURVEY_DIR'),run)
