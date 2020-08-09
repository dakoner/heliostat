import sys
from PyQt5.QtSerialPort import QSerialPort
from PyQt5 import QtCore

class QRAMPSObject(QtCore.QObject):
    messageSignal = QtCore.pyqtSignal(str)
    def __init__(self, *args, **kwargs):
        super(QtCore.QObject, self).__init__(*args, **kwargs)

        self.serial = QSerialPort()
        port = "/dev/ttyUSB0"
        self.serial.setPortName(port)
        if self.serial.open(QtCore.QIODevice.ReadWrite):
            self.serial.setDataTerminalReady(True)
            self.serial.setBaudRate(115200)
            self.serial.readyRead.connect(self.on_serial_read)
        else:
            print("Failed to open serial port")

        
    def send_line(self, line):
        b = bytearray(line + '\r', 'utf-8')
        self.serial.writeData(b)
        
    def on_serial_read(self, *args):
        data = self.serial.readAll()
        decoded = data.data().decode('US_ASCII')
        self.messageSignal.emit(decoded)
