import os
import glob
import logging

import numpy as np
from matplotlib import pyplot as plt

from photometry import Catalogue, setup_logging, utils


output_dir = os.path.join(os.environ['CSCRATCH'],'legacysim','dr9','cosmos','merged')
deep_fn = os.path.join(output_dir,'deep.fits')
subs = range(80,90)
sub_fns = [os.path.join(output_dir,'sub_{:d}.fits'.format(isub)) for isub in subs]
dr9_fn = os.path.join(output_dir,'dr9.fits')
hsc_dir = '/global/cfs/cdirs/desi/target/analysis/truth/parent'
hsc_fn = os.path.join(hsc_dir,'hsc-pdr2-dud-cosmos-reduced.fits')
truth_fn = os.path.join(os.getenv('HOME'),'photometry','truth_cosmos_deep.fits')

bands = ['g','r','z','w1','w2']
keep = ['ra','dec','brick_primary','release','brickname','objid','maskbits']
keep += ['flux_{}'.format(b) for b in bands]
keep += ['nobs_{}'.format(b) for b in bands]
keep += ['flux_ivar_{}'.format(b) for b in bands]
keep += ['fiberflux_{}'.format(b) for b in bands[:3]]
keep += ['type','sersic','shape_r','shape_e1','shape_e2']
keep += ['galdepth_{}'.format(b) for b in bands[:3]]
keep += ['mw_transmission_{}'.format(b) for b in bands]
keep += ['ebv']


logger = logging.getLogger('make_truth')


def get_catalog(fn):
    catalog = Catalogue.load_fits(fn,keep=keep)
    return catalog[catalog['brick_primary']]


def match_catalogs(deep, hsc, distance_upper_bound=1./3600.):
    index_hsc = utils.match_ra_dec([deep['ra'],deep['dec']],radec2=[hsc['ra'],hsc['dec']],nn=1,distance_upper_bound=distance_upper_bound,degree=True)
    index_deep = np.arange(deep.size)
    mask = index_hsc < hsc.size
    index_hsc = index_hsc[mask]
    index_deep = index_deep[mask]
    logger.info('Matching {:d} sources / {:d} (cosmos) and {:d} (hsc)'.format(index_hsc.size,deep.size,hsc.size))
    logger.info('{:.3f} (cosmos) and {:.3f} (hsc)'.format(index_hsc.size/deep.size,index_hsc.size/hsc.size))
    catalog = deep.deepcopy()
    #catalog = deep[index_deep]
    for field in ['object_id']:
        catalog['hsc_{}'.format(field)] = - catalog.ones(dtype=hsc[field].dtype)
        catalog['hsc_{}'.format(field)][index_deep] = hsc[field][index_hsc]
    for field in ['ra','dec','demp_photoz_best','mizuki_photoz_best']:
        catalog['hsc_{}'.format(field)] = np.nan*catalog.ones(dtype=hsc[field].dtype)
        catalog['hsc_{}'.format(field)][index_deep] = hsc[field][index_hsc]
    return catalog


def fill_catalog(catalog):
    for b in bands[:3]:
        catalog['brick_galdepth_{}'.format(b)] = utils.digitized_statistics(catalog['brickname'],values=catalog['galdepth_{}'.format(b)],statistic='median')
        catalog['{}fiber'.format(b)] = utils.flux_to_mag(catalog['fiberflux_{}'.format(b)]/catalog['mw_transmission_{}'.format(b)])
    for b in bands:
        catalog[b] = utils.flux_to_mag(catalog['flux_{}'.format(b)]/catalog['mw_transmission_{}'.format(b)])
    catalog['shape_ba'],catalog['shape_phi'] = utils.get_shape_ba_phi(catalog['shape_e1'],catalog['shape_e2'])
    return catalog


if __name__ == '__main__':

    write_input = True
    write_matched = True
    setup_logging()

    if write_input:
        base_dir = '/global/project/projectdirs/cosmo/work/legacysurvey/dr9.1.1/tractor/'
        fns = glob.glob(os.path.join(base_dir,'*','tractor-*.fits'))
        catalog = 0
        #setup_logging('warning')
        logger.info('Found {:d} tractor catalogs'.format(len(fns)))
        for ifn,fn in enumerate(fns):
            if ifn % (len(fns)//20) == 0: logger.info('{}/{}'.format(ifn,len(fns)))
            catalog += get_catalog(fn)
        catalog.save_fits(deep_fn)

        base_dir = '/global/cscratch1/sd/dstn/dr9-cosmos-subs/'
        for isub,sub_fn in zip(subs,sub_fns):
            fns = glob.glob(os.path.join(base_dir,str(isub),'tractor','*','tractor-*.fits'))
            catalog = 0
            for ifn,fn in enumerate(fns): catalog += get_catalog(fn)
            catalog.save_fits(sub_fn)

        base_dir = '/global/cfs/cdirs/cosmo/data/legacysurvey/dr9/south/tractor'
        bricknames = np.unique(Catalogue.load_fits(deep_fn,keep=['brickname'])['brickname'])
        catalog = 0
        for brickname in bricknames:
            fn = os.path.join(base_dir,brickname[:3],'tractor-{}.fits'.format(brickname))
            catalog += get_catalog(fn)
        catalog.save_fits(dr9_fn)

    if write_matched:
        subs = sum([Catalogue.load_fits(sub_fn) for sub_fn in sub_fns])
        deep = Catalogue.load_fits(deep_fn)
        dr9 = Catalogue.load_fits(dr9_fn)

        catalogs = {'subs':subs,'deep':deep,'dr9':dr9}
        for catalog in catalogs.values():
            fill_catalog(catalog)

        hsc = Catalogue.load_fits(hsc_fn)
        catalog = match_catalogs(deep,hsc)
        catalog.save(truth_fn)