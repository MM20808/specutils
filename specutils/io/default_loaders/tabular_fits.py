import logging
import os

import numpy as np

from astropy.io import fits
from astropy.nddata import StdDevUncertainty
from astropy.table import Table
import astropy.units as u
from astropy.wcs import WCS

from ...spectra import Spectrum1D
from ..registers import data_loader, custom_writer
from ..parsing_utils import (generic_spectrum_from_table,
                             spectrum_from_column_mapping)

__all__ = ['tabular_fits_loader', 'tabular_fits_writer']


def identify_tabular_fits(origin, *args, **kwargs):
    # check if file can be opened with this reader
    # args[0] = filename
    # fits.open(args[0]) = hdulist
    return (isinstance(args[0], str) and
            # check if file is .fits
            fits.connect.is_fits(origin, *args) and
            # check hdulist has more than one extension
            len(fits.open(args[0])) > 1 and
            # check if fits has BinTable extension
            isinstance(fits.open(args[0])[1], fits.BinTableHDU) and not
            (fits.getheader(args[0])['TELESCOP'] == 'SDSS 2.5-M' and
             fits.getheader(args[0])['FIBERID'] > 0) and not
            (fits.getheader(args[0])['TELESCOP'] == 'HST' and
             fits.getheader(args[0])['INSTRUME'] in ('COS', 'STIS')) and not
            (fits.getheader(args[0])['TELESCOP'] == 'JWST')
            )


@data_loader("tabular-fits", identifier=identify_tabular_fits,
             dtype=Spectrum1D, extensions=['fits'])
def tabular_fits_loader(file_name, column_mapping=None, hdu=1, **kwargs):
    """
    Load spectrum from a FITS file.

    Parameters
    ----------
    file_name: str
        The path to the FITS file
    hdu: int
        The HDU of the fits file (default: 1st extension) to read from
    column_mapping : dict
        A dictionary describing the relation between the FITS file columns
        and the arguments of the `Spectrum1D` class, along with unit
        information. The dictionary keys should be the FITS file column names
        while the values should be a two-tuple where the first element is the
        associated `Spectrum1D` keyword argument, and the second element is the
        unit for the ASCII file column::

            column_mapping = {'FLUX': ('flux', 'Jy')}

    Returns
    -------
    data: Spectrum1D
        The spectrum that is represented by the data in this table.
    """
    # Parse the wcs information. The wcs will be passed to the column finding
    # routines to search for spectral axis information in the file.
    with fits.open(file_name) as hdulist:
        wcs = WCS(hdulist[hdu].header)

    tab = Table.read(file_name, format='fits', hdu=hdu)

    # If no column mapping is given, attempt to parse the file using
    # unit information
    if column_mapping is None:
        return generic_spectrum_from_table(tab, wcs=wcs, **kwargs)

    return spectrum_from_column_mapping(tab, column_mapping, wcs=wcs)


@custom_writer("tabular-fits")
def tabular_fits_writer(spectrum, file_name, update_header=False, **kwargs):
    """
    Write spectrum to BINTABLE extension of a FITS file.

    Parameters
    ----------
    spectrum: Spectrum1D
    file_name: str
        The path to the FITS file
    update_header: bool
        Update FITS header with all compatible entries in `spectrum.meta`
    """
    flux = spectrum.flux
    disp = spectrum.spectral_axis
    header = spectrum.meta.get('header', fits.header.Header()).copy()

    if update_header:
        hdr_types = (str, int, float, complex, bool,
                     np.floating, np.integer, np.complexfloating, np.bool_)
        header.update([keyword for keyword in spectrum.meta.items() if
                       isinstance(keyword[1], hdr_types)])

    # Strip header of FITS reserved keywords
    for keyword in ['NAXIS', 'NAXIS1', 'NAXIS2']:
        header.remove(keyword, ignore_missing=True)

    # Mapping of spectral_axis types to header TTYPE1
    dispname = disp.unit.physical_type
    if dispname == "length":
        dispname = "wavelength"

    columns = [disp, flux]
    colnames = [dispname, "flux"]
    # Include uncertainty - units to be inferred from spectrum.flux
    if spectrum.uncertainty is not None:
        columns.append(spectrum.uncertainty.quantity)
        colnames.append("uncertainty")

    tab = Table(columns, names=colnames, meta=header)

    tab.write(file_name, format="fits", **kwargs)
