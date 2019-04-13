import pynmea2
import signal
import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtSerialPort import QSerialPort

class QApplication(QtWidgets.QApplication):
    def __init__(self, *args, **kwargs):
        super(QApplication, self).__init__(*args, **kwargs)

        self.main_window = QtWidgets.QMainWindow(parent=None)

        self.main_frame = QtWidgets.QFrame(self.main_window)
        self.main_window.setCentralWidget(self.main_frame)
        self.main_window.show()
        self.layout = QtWidgets.QVBoxLayout(self.main_frame)

        self.serial = QSerialPort()
        port = "/dev/ttyUSB1"
        self.serial.setPortName(port)
        if self.serial.open(QtCore.QIODevice.ReadWrite):
            self.serial.setDataTerminalReady(True)
            self.serial.setBaudRate(4800)
            self.serial.readyRead.connect(self.on_serial_read)

        self.text = QtWidgets.QPlainTextEdit()
        self.text.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.text.setWordWrapMode(QtGui.QTextOption.NoWrap)
        font = QtGui.QFont("nonexistent")
        font.setStyleHint(QtGui.QFont.Monospace)
        self.text.setMinimumWidth(1000)
        self.text.setMinimumHeight(250)
        self.text.setFont(font)
        self.text.setReadOnly(True)
        self.layout.addWidget(self.text)
        
        self.buffer = None

    def on_text_changed(self):
        print("on_text_changed")
        
    def on_serial_read(self, *args):
        if self.serial.canReadLine():
            line = self.serial.readLine()
            decoded = line.data().decode('US_ASCII')
            msg = pynmea2.parse(decoded)
            if (msg.sentence_type == 'GGA'):
                print(msg.latitude, msg.longitude)
            self.text.appendPlainText(decoded.strip())

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    app.exec_()
