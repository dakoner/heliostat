import dateutil.parser
import astropy.coordinates as coord
from astropy.time import Time
import astropy.units as u
import time
import gpsd
import serial

HAS_GPS=True

s = serial.Serial("/dev/ttyUSB0", 115200, timeout=1)
msg = b"[MSG:'$H'|'$X' to unlock]\r\n"
time.sleep(1)
s.write(b"\r\n")

while True:
    l = s.readline()
    print(l)
    if l.startswith(msg):
        break
print("Sending HOME")
s.write(b"$H\r\n")
while True:
    print("Checking for OK")
    l = s.readline()
    print(l)
    if l == b'ok\r\n':
        print("match")
        break
    time.sleep(1)

if HAS_GPS:
    gpsd.connect()

# See the inline docs for GpsResponse for the available data
while True:
    if HAS_GPS:
        packet = gpsd.get_current()
        try:
            lat, lon = packet.position()
            t = dateutil.parser.parse(packet.time)
            now = Time(t)
        except gpsd.NoFixError:
            print("no fix")
            time.sleep(0.25)
            continue
    else:
        lon = -122.394
        lat = 37.654
        now = Time.now()

    loc = coord.EarthLocation(lon=lon * u.deg,
                              lat=lat * u.deg)
    altaz = coord.AltAz(location=loc, obstime=now)
    sun = coord.get_sun(now)
    result = sun.transform_to(altaz)
    xaz = -(90+result.az.degree)
    xalt = -(90-result.alt.degree)
    cmd = b"G0 X%.3f Y%.3f\r\n" % (xaz, xalt)
    s.write(cmd)
    print(cmd)
    print(s.readline())
    time.sleep(1)
