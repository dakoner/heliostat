#!/usr/bin/env python3

import serial
import termios, fcntl, sys, os

fd = sys.stdin.fileno()

oldterm = termios.tcgetattr(fd)
newattr = termios.tcgetattr(fd)
newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
termios.tcsetattr(fd, termios.TCSANOW, newattr)

oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

s = serial.Serial('/dev/ttyUSB0', 115200, timeout=5)
header = s.readline()
print("Header: ", header)


try:
    while True:
        if s.inWaiting() > 0:
            line = s.readline()
            print(line)
        c = sys.stdin.read(1)
        if c != '':
            print("Got character", repr(c))

finally:
    termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
