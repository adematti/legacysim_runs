import os

survey_dir = os.getenv('LEGACY_SURVEY_DIR')
run = 'south'
output_dir = os.path.join(os.getenv('CSCRATCH'),'legacysim','dr9','cosmos','nonoise_{}'.format(run))
randoms_fn = ['/global/cfs/cdirs/cosmo/data/legacysurvey/dr9/randoms/randoms-1-%d.fits' % i for i in range(2)]
truth_fn = os.path.join(os.getenv('HOME'),'photometry','truth_cosmos_deep.fits')
injected_fn = os.path.join(output_dir,'file0_rs0_skip0','injected.fits')
bricklist_fn = 'bricklist_south.txt'
runlist_fn = 'runlist_south.txt'

def get_bricknames():
    return [brickname[:-len('\n')] for brickname in open(bricklist_fn,'r')]

legacypipe_output_dir = os.path.join(os.getenv('LEGACYPIPE_SURVEY_DIR'),run)
