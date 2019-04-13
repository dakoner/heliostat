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
        port = "/dev/ttyUSB0"
        self.serial.setPortName(port)
        if self.serial.open(QtCore.QIODevice.ReadWrite):
            self.serial.setDataTerminalReady(True)
            self.serial.setBaudRate(115200)
            self.serial.readyRead.connect(self.on_serial_read)

        self.text = QtWidgets.QPlainTextEdit()
        self.text.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.text.setWordWrapMode(QtGui.QTextOption.NoWrap)
        font = QtGui.QFont("nonexistent")
        font.setStyleHint(QtGui.QFont.Monospace)
        self.text.setMinimumWidth(500)
        self.text.setMinimumHeight(250)
        self.text.setFont(font)
        self.text.setReadOnly(True)
        self.layout.addWidget(self.text)
        
        self.input = QtWidgets.QLineEdit()
        self.input.setMinimumWidth(500)
        self.input.returnPressed.connect(self.line_entered)
        self.layout.addWidget(self.input)

        self.buffer = None

    def line_entered(self):
        print("line:", self.input.text())
        b = bytearray(self.input.text(), 'utf-8')
        print(b)
        self.serial.writeData(b + b"\r")
    def on_text_changed(self):
        print("on_text_changed")
        
    def on_serial_read(self, *args):
        data = self.serial.readAll()
        if self.buffer:
            decoded = self.buffer + data.data().decode('US_ASCII')
        else:
            decoded = data.data().decode('US_ASCII')
        self.buffer = None
        lines = decoded.split("\r\n")
        for i, line in enumerate(lines):
            if i < len(lines) - 1:
                self.text.appendPlainText(line)
            else:
                self.buffer = line

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    app.exec_()
