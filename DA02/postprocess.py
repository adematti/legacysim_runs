import os
import shutil

import numpy as np
import fitsio
from photometry import Catalogue


base_dir = '/global/cfs/cdirs/desi/users/adematti/legacysim/dr9/SV3/south/file0_rs0_skip0/'
survey_dir = '/global/cfs/cdirs/cosmo/data/legacysurvey/dr9/south/'


def get_ib(b):
    #return np.round(b).astype(np.int32)
    return np.clip(b, 0, 3600 - 1).astype(int)


def add_nobs(in_fn, out_fn):
    catalog = Catalogue.load_fits(in_fn)
    catalog['input_bx'] -= 1
    catalog['input_by'] -= 1
    ibx, iby = get_ib(catalog['input_bx']), get_ib(catalog['input_by'])
    for b in ['g', 'r', 'z']:
        catalog['input_nobs_{}'.format(b)] = np.zeros_like(catalog['nobs_{}'.format(b)])
    bricknames = np.unique(catalog['input_brickname'])
    for ibrick, brickname in enumerate(bricknames):
        print(ibrick, len(bricknames))
        mask = catalog['input_brickname'] == brickname
        for b in ['g', 'r', 'z']:
            fn = os.path.join(base_dir, 'coadd', brickname[:3], brickname, 'legacysurvey-{}-nexp-{}.fits.fz'.format(brickname, b))
            data = fitsio.read(fn)
            catalog['input_nobs_{}'.format(b)][mask] = data[iby[mask], ibx[mask]]
    catalog.save_fits(out_fn)

        
if __name__ == '__main__':

    fn_bak = os.path.join(base_dir, 'merged', 'matched_input_bak.fits')
    fn = os.path.join(base_dir, 'merged', 'matched_input.fits')
    #print(fn)
    ##shutil.copyfile(fn, fn_bak)
    add_nobs(fn_bak, fn)