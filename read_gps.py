import dateutil.parser
import astropy.coordinates as coord
from astropy.time import Time
import astropy.units as u
import time
import pynmea2
import serial


s = serial.Serial("COM6", 115200, timeout=1)
msg = b"[MSG:'$H'|'$X' to unlock]\r\n"
time.sleep(1)
s.write(b"\r\n")

while True:
    l = s.readline()
    print(l)
    if l.startswith(msg):
        time.sleep(1)
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

def getSunPos(latitude, longitude, t):
    loc = coord.EarthLocation(lon=longitude * u.deg,
                              lat=latitude * u.deg)
    now = Time(t)
    altaz = coord.AltAz(location=loc, obstime=now)
    sun = coord.get_sun(now)
    result = sun.transform_to(altaz)
    return result

gpsserial = serial.Serial("COM7", 4800, timeout=1)


# See the inline docs for GpsResponse for the available data
while True:
    
    line = gpsserial.readline()
    decoded = line.decode('UTF-8')
    try:
        msg = pynmea2.parse(decoded)
    except pynmea2.ParseError:
        print("failed to parse")
    else:
        if (msg.sentence_type == 'RMC'):
            result = getSunPos(msg.latitude, msg.longitude, msg.datetime)
            #print(msg.latitude, msg.longitude, msg.datetime, result.alt.degree, result.az.degree)
            
            xaz = result.az.degree-90
            xaz = 0
            xalt = (90-result.alt.degree)
            alt = 0
            cmd = b"G0 X%.3f Y%.3f\r\n" % (xaz, xalt)
            s.write(cmd)
            print(cmd)
            print(s.readline())
