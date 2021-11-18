import argparse
import logging
import numpy as np
try:
    from legacysim import SimCatalog, BrickCatalog, utils, setup_logging
except ImportError:
    pass

logger = logging.getLogger('preprocessing')

def get_maskbit(catalog, bits=[1, 11, 12, 13]):
    # BRIGHT, MEDIUM, GALAXY, CLUSTER
    mask = catalog.trues()
    for bit in bits:
        mask &= (catalog.get('maskbits') & 2**bit) == 0
    return mask

def get_mask_depth(catalog, gth=4000., rth=2000., zth=500.):
    #mask = (catalog.get('brick_galdepth_g') > gth)
    #mask &= (catalog.get('brick_galdepth_r') > rth)
    #mask &= (catalog.get('brick_galdepth_z') > zth)
    mask = (catalog.get('galdepth_g') > gth)
    mask &= (catalog.get('galdepth_r') > rth)
    mask &= (catalog.get('galdepth_z') > zth)
    return mask

def isELG_colors(gflux=None, rflux=None, zflux=None, w1flux=None,
                 w2flux=None, gfiberflux=None, south=True, primary=None,
                 gmarg=0., grmarg=0., rzmarg=0.):
    """
    Apply ELG selection with box enlarged by ``gmarg``, ``grmarg``, ``rzmarg``.

    Base selection from https://github.com/desihub/desitarget/blob/master/py/desitarget/cuts.py.
    """
    if primary is None:
        primary = np.ones_like(rflux, dtype='?')
    elg = primary.copy()

    # ADM work in magnitudes instead of fluxes. NOTE THIS IS ONLY OK AS
    # ADM the snr masking in ALL OF g, r AND z ENSURES positive fluxes.
    g = 22.5 - 2.5*np.log10(gflux.clip(1e-16))
    r = 22.5 - 2.5*np.log10(rflux.clip(1e-16))
    z = 22.5 - 2.5*np.log10(zflux.clip(1e-16))
    gfib = 22.5 - 2.5*np.log10(gfiberflux.clip(1e-16))

    # ADM cuts shared by the northern and southern selections.
    elg &= g > 20 - gmarg                # bright cut.
    elg &= r - z > 0.15 - rzmarg         # blue cut.
#    elg &= r - z < 1.6 + rzmarg         # red cut.

    # ADM cuts that are unique to the north or south. Identical for sv3
    # ADM but keep the north/south formalism in case we use it later.
    if south:
        elg &= gfib < 24.1 + gmarg  # faint cut.
        elg &= g - r < 0.5*(r - z) + 0.1 + grmarg  # remove stars, low-z galaxies.
    else:
        elg &= gfib < 24. + gmarg  # faint cut.
        elg &= g - r < 0.5*(r - z) + 0.1 + grmarg  # remove stars, low-z galaxies.

    # ADM separate a low-priority and a regular sample.
    elgvlo = elg.copy()

    # ADM low-priority OII flux cut.
    elgvlo &= g - r < -1.2*(r - z) + 1.6 + grmarg
    elgvlo &= g - r >= -1.2*(r - z) + 1.3 - grmarg

    # ADM high-priority OII flux cut.
    elg &= g - r < -1.2*(r - z) + 1.3 + grmarg

    return elgvlo, elg

def get_truth(truth_fn, south=True):
    """Build truth table."""
    logger.info('Reading truth file %s',truth_fn)
    truth = SimCatalog(truth_fn)
    mask = get_maskbit(truth)
    mask = get_mask_depth(truth)
    mask &= isELG_colors(south=south,gmarg=0.5,grmarg=0.5,rzmarg=0.5,**{'%sflux' % b:utils.mag2nano(truth.get(b)) for b in ['g','r','z','gfiber']})[0]
    for b in ['g','r','z','gfiber']:
        mask &= (~np.isnan(truth.get(b))) & (~np.isinf(truth.get(b)))
    logger.info('Target selection: %d/%d objects',mask.sum(),mask.size)
    truth = truth[mask]
    return truth

def sample_from_truth(randoms, truth, rng=None, seed=None):
    """Sample random photometry from truth table."""
    if rng is None:
        logger.info('Using seed = %d',seed)
        rng = np.random.RandomState(seed=seed)

    ind = rng.randint(low=0,high=truth.size,size=randoms.size)

    for field in ['objid','g','r','z','shape_r','sersic','shape_ba','shape_phi']:
        randoms.set(field,truth.get(field)[ind])

    for b in ['g','r','z']:
        transmission = 10**(-0.4*randoms.get_extinction(b,camera='DES'))
        randoms.set('mw_transmission_%s' % b,transmission)
        flux = utils.mag2nano(randoms.get(b))*transmission
        randoms.set('flux_%s' % b,flux)

    randoms.shape_e1,randoms.shape_e2 = utils.get_shape_e1_e2(randoms.get('shape_ba'),randoms.get('shape_phi'))

    randoms.fill_legacysim(seed=seed)

    return randoms

def get_legacysurvey_randoms(randoms_fn, truth_fn, bricknames=[], seed=None):
    """Build legacysim catalog of injected sources from legacysurvey randoms and truth table."""
    if not isinstance(randoms_fn,list): randoms_fn = [randoms_fn]
    randoms = 0
    for fn in randoms_fn:
        logger.info('Reading randoms file %s',fn)
        randoms += SimCatalog(fn)
    logger.info('Selecting randoms in %s',bricknames)
    mask = np.in1d(randoms.brickname,bricknames)
    randoms = randoms[mask]
    randoms.rename('targetid','id')
    logger.info('Selected random catalog of size = %d.',randoms.size)
    #randoms.keep_columns('id','ra','dec','maskbits','photsys','brickname')

    for photsys in ['N','S']:
        truth = get_truth(truth_fn,south=photsys=='S')
        mask = randoms.photsys == photsys
        logger.info('Found %d randoms in %s.',mask.sum(),photsys)
        if mask.any():
            randoms.fill(sample_from_truth(randoms[mask],truth,seed=seed),index_self=mask,index_other=None)

    return randoms

if __name__ == '__main__':

    setup_logging()

    parser = argparse.ArgumentParser(description='legacysim preprocessing')
    parser.add_argument('-d','--do',nargs='*',type=str,choices=['bricklist','injected'],default=[],required=False,help='What should I do?')
    parser.add_argument('-r','--run',type=str,choices=['north','south'],required=True,help='Run?')
    opt = parser.parse_args()

    if opt.run == 'north':
        import settings_north as settings
    else:
        import settings_south as settings

    if 'bricklist' in opt.do:
        write_bricklist(settings.injected_fn,settings.bricklist_fn,south=settings.run=='south')

    if 'injected' in opt.do:
        injected = 0
        for iseed,fn in enumerate(settings.randoms_fn):
            injected += get_legacysurvey_randoms(fn,settings.truth_fn,bricknames=settings.get_bricknames(),seed=42*(iseed+1))
        injected.writeto(settings.injected_fn)
