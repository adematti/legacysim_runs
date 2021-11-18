import os

run = 'north'
survey_dir = os.getenv('LEGACY_SURVEY_DIR')
output_dir = os.path.join(os.getenv('CSCRATCH'),'legacysim','dr9','SV3',run)
truth_fn = os.path.join(os.getenv('HOME'),'photometry','truth_cosmos_deep.fits')
injected_fn = os.path.join(output_dir,'file0_rs0_skip0','injected.fits')
bricklist_fn = 'bricklist_{}.txt'.format(run)
#runlist_fn = 'runlist_{}.txt'.format(run)
runlist_fn = 'runlist_{}_7.txt'.format(run)

def get_bricknames():
    return [brickname[:-len('\n')] for brickname in open(bricklist_fn,'r')]

legacypipe_output_dir = os.path.join(os.getenv('LEGACYPIPE_SURVEY_DIR'),run)
