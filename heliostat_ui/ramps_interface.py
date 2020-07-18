import sys
from PyQt5.QtSerialPort import QSerialPort
from PyQt5 import QtWidgets, QtCore, QtGui
from ramps_qobject import QRAMPSObject

class QRAMPSTerminal(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(QtWidgets.QWidget, self).__init__(*args, **kwargs)

        self.ramps_qobject = QRAMPSObject()
        self.ramps_qobject.messageSignal.connect(self.on_serial_read)

        self.layout = QtWidgets.QVBoxLayout(self)

        self.info_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.info_layout)

        font = QtGui.QFont("nonexistent")
        font.setStyleHint(QtGui.QFont.Monospace)
        font.setPointSize(10)
        self.text = QtWidgets.QPlainTextEdit()
        self.text.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.text.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.text.setMinimumWidth(1500)
        self.text.setMinimumHeight(1000)
        self.text.setFont(font)
        self.text.setReadOnly(True)
        self.layout.addWidget(self.text)
        
        self.input = QtWidgets.QLineEdit()
        self.input.setMinimumWidth(500)
        self.input.returnPressed.connect(self.line_entered)
        self.layout.addWidget(self.input)
    
    def line_entered(self):
        line = self.input.text()
        self.text.insertPlainText("Sent: " + line)
        self.text.insertPlainText("\n")
        self.ramps_qobject.send_line(line)
        self.input.clear()

    def on_serial_read(self, data):
        self.text.insertPlainText(data)
        self.text.verticalScrollBar().setValue(self.text.verticalScrollBar().maximum())

def main():
    app = QtWidgets.QApplication(sys.argv)
    main = QRAMPSTerminal()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':      
    main()