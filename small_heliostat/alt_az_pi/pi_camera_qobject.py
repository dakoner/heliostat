#!/usr/bin/python3
from PyQt5.QtCore import QObject, pyqtSignal
import picamera
RESOLUTION=800, 480
 
class QPiCamera(QObject):
    messageSignal = pyqtSignal(bytes)

    def __init__(self, parent=None):
        super(QPiCamera, self).__init__(parent)
        
    def loop(self):
        with picamera.PiCamera(resolution=RESOLUTION, framerate=25) as camera:
            with picamera.CircularIO(size=RESOLUTION[0]*RESOLUTION[1]*3) as stream:
                for frame in camera.capture_continuous(stream, format='bgr'):
                    stream.seek(0)
                    self.messageSignal.emit(stream.read())
