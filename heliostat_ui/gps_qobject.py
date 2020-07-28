from PyQt5.QtSerialPort import QSerialPort
from PyQt5 import QtCore
import pynmea2
import datetime
import signal
from sun_pos import getSunPos
class GPSQObject(QtCore.QObject):
    messageSignal = QtCore.pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(QtCore.QObject, self).__init__(*args, **kwargs)

        self.serial = QSerialPort()
        port = "COM7"
        self.serial.setPortName(port)
        if self.serial.open(QtCore.QIODevice.ReadWrite):
            self.serial.setDataTerminalReady(True)
            self.serial.setBaudRate(4800)
            self.serial.readyRead.connect(self.on_serial_read)

    def on_serial_read(self, *args):
        if self.serial.canReadLine():
            line = self.serial.readLine()
            try:
                decoded = bytes(line).decode()
            except UnicodeDecodeError:
                pass
            else:
                self.messageSignal.emit(decoded)


    
class Tui(QtCore.QObject):

    def __init__(self, app):
        super(Tui, self).__init__()

        self.app = app

        self.gps = GPSQObject()
        self.gps.messageSignal.connect(self.on_serial_read)

    def on_serial_read(self, data):
        try:
            msg = pynmea2.parse(data)
        except pynmea2.ParseError:
            print("failed to parse")
        else:
            if (msg.sentence_type == 'RMC'):
                result = getSunPos(msg.latitude, msg.longitude, msg.datetime)
                print(msg.latitude, msg.longitude, msg.datetime, result.alt.degree, result.az.degree)

if __name__ == "__main__":
    import sys
    app = QtCore.QCoreApplication(sys.argv)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    tui = Tui(app)
    sys.exit(app.exec_())