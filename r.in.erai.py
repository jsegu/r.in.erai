#!/usr/bin/env python

"""
MODULE:     r.in.erai

AUTHOR(S):  Julien Seguinot <seguinot@vaw.baug.ethz.ch>.

PURPOSE:    Import ERA-Interim [1] Reanalysis fields netCDF data files.

COPYRIGHT:  (c) 2016 Julien Seguinot

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Todo:
# * (0.1)
#  - upload to GRASS repo/wiki
#  - add minimal HTML docs

#%Module
#% description: Import ERA-Interim Reanalysis fields netCDF data files.
#% keywords: raster import ERA Interim
#%End

#%option
#% key: input
#% type: string
#% gisprompt: old,file,input
#% description: NetCDF file to be imported
#% required: yes
#%end
#%option
#% key: output
#% type: string
#% gisprompt: old,file,input
#% description: Name or prefix for output raster maps
#% required: yes
#%end
#%option
#% key: var
#% type: string
#% description: NetCDF variable to be imported
#% required: yes
#%end

import numpy as np              # [1]
from netCDF4 import Dataset     # [2]
from grass.script import core as grass
from grass.script import array as garray


def main():
    """Main function, called at execution time"""

    # parse arguments
    inputfile = options['input']
    outputmap = options['output']
    var = options['var']

    # read NetCDF data
    nc = Dataset(inputfile, 'r')
    lon = nc.variables['longitude'][:]
    lat = nc.variables['latitude'][:]
    z = nc.variables[var][:]
    nc.close()

    # check that coordinates are regular
    dlon = np.diff(lon)
    dlat = np.diff(lat)
    dlon0 = dlon[0]
    dlat0 = dlat[0]
    assert (dlon == dlon0).all()
    assert (dlat == dlat0).all()

    # crop illegal latitudes
    lat = lat[np.abs(lat) < 90-np.abs(dlat0)/2]

    # rotate longitudes and sort
    lon -= (lon > 180)*360
    lon_args = lon.argsort()
    lat_args = lat.argsort()[::-1]

    # crop and rotate data
    lat = lat[lat_args]
    lon = lon[lon_args]
    z = z[:, lat_args, :][:, :, lon_args]

    # set temporary region
    w = lon[-1] + dlon0/2
    e = lon[0] - dlon0/2
    s = lat[-1] - dlat0/2
    n = lat[0] + dlat0/2
    rows = len(lat)
    cols = len(lon)
    grass.run_command('g.region', w=w, e=e, s=s, n=n, rows=rows, cols=cols)

    # import time-independent data as such
    a = garray.array()
    if z.shape[0] == 1:
        a[:] = z[0]
        grass.message("Importing <%s> ..." % outputmap)
        a.write(mapname=outputmap, overwrite=True, null=-32767)

    # otherwise import each time slice
    else:
        for (i, data) in enumerate(z):
            mapname = outputmap + '%02i' % (i+1)
            grass.message("Importing <%s> ..." % mapname)
            a[:] = data
            a.write(mapname=mapname, overwrite=True, null=-32767)

if __name__ == "__main__":
    options, flags = grass.parser()
    main()

# Links
# [1] http://www.ecmwf.int/en/research/climate-reanalysis/era-interim
# [2] http://numpy.scipy.org
# [3] http://github.com/Unidata/netcdf4-python

