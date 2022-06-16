import os
import argparse
import logging

import numpy as np
try:
    from legacysim import SimCatalog, BrickCatalog, utils, setup_logging
    from legacypipe.survey import LegacySurveyData, wcs_for_brick
except ImportError:
    pass

from grid import HexGrid

logger = logging.getLogger('preprocessing')


def get_imaging_maskbits(bitnamelist=None):
    """Return MASKBITS names and bits from the Legacy Surveys.
    Parameters
    ----------
    bitnamelist : :class:`list`, optional, defaults to ``None``
        If not ``None``, return the bit values corresponding to the
        passed names. Otherwise, return the full MASKBITS dictionary.
    Returns
    -------
    :class:`list` or `dict`
        A list of the MASKBITS values if `bitnamelist` is passed,
        otherwise the full MASKBITS dictionary of names-to-values.
    Notes
    -----
    - For the definitions of the mask bits, see, e.g.,
      https://www.legacysurvey.org/dr8/bitmasks/#maskbits
    """
    bitdict = {"BRIGHT": 1, "ALLMASK_G": 5, "ALLMASK_R": 6, "ALLMASK_Z": 7,
               "BAILOUT": 10, "MEDIUM": 11, "GALAXY": 12, "CLUSTER": 13}

    # ADM look up the bit value for each passed bit name.
    if bitnamelist is not None:
        return [bitdict[bitname] for bitname in bitnamelist]

    return bitdict


def get_default_maskbits(bgs=False, mws=False):
    """Return the names of the default MASKBITS for targets.
    Parameters
    ----------
    bgs : :class:`bool`, defaults to ``False``.
        If ``True`` load the "default" scheme for Bright Galaxy Survey
        targets. Otherwise, load the default for other target classes.
    mws : :class:`bool`, defaults to ``False``.
        If ``True`` load the "default" scheme for Milky Way Survey
        targets. Otherwise, load the default for other target classes.
    Returns
    -------
    :class:`list`
        A list of the default MASKBITS names for targets.
    Notes
    -----
    - Only one of `bgs` or `mws` can be ``True``.
    """
    if bgs and mws:
        msg = "Only one of bgs or mws can be passed as True"
        log.critical(msg)
        raise ValueError(msg)
    if bgs:
        return ["BRIGHT", "CLUSTER"]
    if mws:
        return ["BRIGHT", "GALAXY"]

    return ["BRIGHT", "GALAXY", "CLUSTER"]


def imaging_mask(maskbits, bitnamelist=get_default_maskbits(),
                 bgsmask=False, mwsmask=False):
    """Apply the 'geometric' masks from the Legacy Surveys imaging.
    Parameters
    ----------
    maskbits : :class:`~numpy.ndarray` or ``None``
        General array of `Legacy Surveys mask`_ bits.
    bitnamelist : :class:`list`, defaults to func:`get_default_maskbits()`
        List of Legacy Surveys mask bits to set to ``False``.
    bgsmask : :class:`bool`, defaults to ``False``.
        Load the "default" scheme for Bright Galaxy Survey targets.
        Overrides `bitnamelist`.
    bgsmask : :class:`bool`, defaults to ``False``.
        Load the "default" scheme for Milky Way Survey targets.
        Overrides `bitnamelist`.
    Returns
    -------
    :class:`~numpy.ndarray`
        A boolean array that is the same length as `maskbits` that
        contains ``False`` where any bits in `bitnamelist` are set.
    Notes
    -----
    - Only one of `bgsmask` or `mwsmask` can be ``True``.
    """
    # ADM default for the BGS or MWS..
    if bgsmask or mwsmask:
        bitnamelist = get_default_maskbits(bgs=bgsmask, mws=mwsmask)

    # ADM get the bit values for the passed (or default) bit names.
    bits = get_imaging_maskbits(bitnamelist)

    # ADM Create array of True and set to False where a mask bit is set.
    mb = np.ones_like(maskbits, dtype='?')
    for bit in bits:
        mb &= ((maskbits & 2**bit) == 0)

    return mb


def custom_imaging_mask(maskbits, bits=[1, 5, 6, 7, 11, 12, 13]):
    # BRIGHT, ALLMASK_G,R,Z, MEDIUM, GALAXY, CLUSTER
    mb = np.ones_like(maskbits, dtype='?')
    for bit in bits:
        mb &= ((maskbits & 2**bit) == 0)

    return mb


def notinELG_mask(maskbits=None, gsnr=None, rsnr=None, zsnr=None,
                  gnobs=None, rnobs=None, znobs=None, primary=None):
    """Standard set of masking cuts used by all ELG target selection classes.
    (see :func:`~desitarget.cuts.set_target_bits` for parameters).
    """
    if primary is None:
        primary = np.ones_like(maskbits, dtype='?')
    elg = primary.copy()

    # ADM good signal-to-noise in all bands.
    elg &= (gsnr > 0) & (rsnr > 0) & (zsnr > 0)

    # ADM observed in every band.
    elg &= (gnobs > 0) & (rnobs > 0) & (znobs > 0)

    # ADM default mask bits from the Legacy Surveys not set.
    #elg &= imaging_mask(maskbits)
    elg &= custom_imaging_mask(maskbits)

    return elg


def get_mask_depth(catalog, gth=4000., rth=2000., zth=500.):
    # Anand's cuts
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

    Main selection from https://github.com/desihub/desitarget/blob/7786db0931d23ed20de7ef37a6f07a52072e11ab/py/desitarget/cuts.py#L578
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


def get_mask_ts(catalog, priority='all', **kwargs):
    mask_low, mask_high = isELG_colors(**{'%sflux' % b:utils.mag2nano(catalog.get(b)) for b in ['g','r','z','gfiber']},**kwargs)
    if priority == 'low': return mask_low
    if priority == 'high': return mask_high
    return (mask_low | mask_high)


def get_truth(truth_fn, south=True):
    """Build truth table."""
    logger.info('Reading truth file %s',truth_fn)
    truth = SimCatalog(truth_fn)
    snr = {b: truth.get('flux_%s' % b) * np.sqrt(truth.get('flux_ivar_%s' % b)) for b in ['g','r','z']}
    mask = truth.get('hsc_object_id') >= 0
    mask &= notinELG_mask(maskbits=truth.maskbits,gsnr=snr['g'],rsnr=snr['r'],zsnr=snr['z'],gnobs=truth.nobs_g,rnobs=truth.nobs_r,znobs=truth.nobs_z)
    mask &= get_mask_depth(truth)
    mask &= get_mask_ts(truth,south=south,gmarg=1.2,grmarg=0.8,rzmarg=0.5)
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
    
    for field in ['objid','g','r','z','gfiber','rfiber','zfiber','shape_r','sersic','shape_ba','shape_phi','hsc_object_id','hsc_demp_photoz_best','hsc_mizuki_photoz_best']:
        randoms.set(field,truth.get(field)[ind])

    for b in ['g','r','z']:
        transmission = 10**(-0.4*randoms.get_extinction(b,camera='DES'))
        randoms.set('mw_transmission_%s' % b,transmission)
        flux = utils.mag2nano(randoms.get(b))*transmission
        randoms.set('flux_%s' % b,flux)

    randoms.shape_phi = rng.uniform(0.,np.pi,randoms.size)
    randoms.shape_e1,randoms.shape_e2 = utils.get_shape_e1_e2(randoms.get('shape_ba'),randoms.shape_phi)

    seed = rng.randint(int(2**32 - 1))
    randoms.fill_legacysim(seed=seed)

    return randoms


def get_legacysurvey_randoms(randoms_fn, truth_fn, bricknames=(), rng=None, seed=None):
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
            randoms.fill(sample_from_truth(randoms[mask],truth,rng=rng,seed=seed),index_self=mask,index_other=None)

    return randoms


def get_grid_in_brick(survey, brickname, rng=None, seed=None):
    
    brick = survey.get_brick_by_name(brickname)
    brickwcs = wcs_for_brick(brick)
    W, H, pixscale = brickwcs.get_width(), brickwcs.get_height(), brickwcs.pixel_scale()
    
    if rng is None:
        logger.info('Using seed = %d',seed)
        rng = np.random.RandomState(seed=seed)
    
    logger.info('Generating grid for %s' % brickname)
    
    offset = rng.uniform(0.,1.,size=2)
    side = 144 # 60*0.262 = 15.72 arcsec
    # for HexGrid spacing is defined as radius... here we rather want space along x and y, so divide by correct factor
    # we also alternate start of horizontal lines depending on brick column, to allow for better transition between bricks
    grid = HexGrid(spacing=side/(2.*np.tan(np.pi/6)),shape=(W,H),shift=brick.brickcol % 2)
    grid.positions += offset + side/2 # we add random pixel fraction offset, then side/2 because grid.positions start at 0
    positions = grid._mask(grid.positions)

    catalog = SimCatalog(size=positions.shape[0])
    catalog.bx, catalog.by = positions.T
    
    catalog.ra, catalog.dec = brickwcs.pixelxy2radec(catalog.bx,catalog.by)
    catalog.id = catalog.index()
    catalog.brickname = catalog.full(brickname)
    mask_primary = (catalog.ra >= brick.ra1) * (catalog.ra < brick.ra2) * (catalog.dec >= brick.dec1) * (catalog.dec < brick.dec2)
    
    return catalog[mask_primary]

    
def get_grid_randoms(truth_fn, bricknames=(), south=True, seed=None):
    
    rng = np.random.RandomState(seed=seed)
    randoms = 0
    survey = LegacySurveyData(survey_dir='/global/cfs/cdirs/cosmo/work/legacysurvey/dr9')
    for iseed,brickname in enumerate(bricknames):
        randoms += get_grid_in_brick(survey,brickname,rng=rng)
    
    randoms.photsys = randoms.full('S' if south else 'N')
    truth = get_truth(truth_fn,south=south)
    randoms.fill(sample_from_truth(randoms,truth,rng=rng),index_self=None,index_other=None)

    return randoms
    


if __name__ == '__main__':
    
    setup_logging()

    parser = argparse.ArgumentParser(description='legacysim preprocessing')
    parser.add_argument('-d','--do',nargs='*',type=str,choices=['bricklist','injected'],default=[],required=False,help='What should I do?')
    parser.add_argument('-r','--run',type=str,choices=['north','south'],required=True,help='Run?')
    opt = parser.parse_args()

    south = opt.run == 'south'
    if not south:
        import settings_north as settings
    else:
        import settings_south as settings

    if 'injected' in opt.do:
        injected = get_grid_randoms(settings.truth_fn,bricknames=settings.get_bricknames(),south=south,seed=42) 
        #injected = 0
        #for iseed,fn in enumerate(settings.randoms_fn):
        #    injected += get_legacysurvey_randoms(fn,settings.truth_fn,bricknames=settings.get_bricknames(),seed=42*(iseed+1))
        injected.writeto(settings.injected_fn)