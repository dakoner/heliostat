import astropy.coordinates as coord
from astropy.time import Time
import astropy.units as u

import datetime

def getSunPos(latitude, longitude, t):
    loc = coord.EarthLocation(lon=longitude * u.deg,
                              lat=latitude * u.deg)
    now = Time(t)
    altaz = coord.AltAz(location=loc, obstime=now)
    sun = coord.get_sun(now)
    result = sun.transform_to(altaz)
    return result

if __name__ == '__main__':
    print(getSunPos(40, 40, datetime.datetime.now()))