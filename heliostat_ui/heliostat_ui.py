from PyQt5 import QtWidgets, QtCore, uic
import sys 
import os
from ramps_qobject import QRAMPSObject

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        #Load the UI Page
        uic.loadUi('heliostat.ui', self)
        self.down_button.clicked.connect(self.down_button_clicked)
        self.up_button.clicked.connect(self.up_button_clicked)
        self.right_button.clicked.connect(self.right_button_clicked)
        self.left_button.clicked.connect(self.left_button_clicked)
        self.home_x_button.clicked.connect(self.home_x_button_clicked)
        self.home_y_button.clicked.connect(self.home_y_button_clicked)

        self.ramps_qobject = QRAMPSObject()
        self.ramps_qobject.messageSignal.connect(self.on_serial_read)

        # TODO(dek): instead of a timer, use state machine that waits for the expected startup string
        self.timer = QtCore.QTimer.singleShot(1000, self.setRelativeMode)
        self.lineEdit.hide()
        self.lineEdit.returnPressed.connect(self.line_entered)

    def setRelativeMode(self):
        self.send_line("G91")
        self.lineEdit.show()


    def line_entered(self):
        line = self.lineEdit.text()
        self.send_line(line)
        self.lineEdit.clear()

    def send_line(self, line):
        self.ramps_output.insertPlainText("Sent: " + line)
        self.ramps_output.insertPlainText("\n")
        self.ramps_qobject.send_line(line)

    def on_serial_read(self, data):
        self.ramps_output.insertPlainText(data)
        self.ramps_output.verticalScrollBar().setValue(self.ramps_output.verticalScrollBar().maximum())

    def down_button_clicked(self):
        self.send_line("G0 Y-10")
    
    def up_button_clicked(self):
        self.send_line("G0 Y10")

    def right_button_clicked(self):
        self.send_line("G0 X10")
    
    def left_button_clicked(self):
        self.send_line("G0 X-10")
  
    def home_x_button_clicked(self):
        self.send_line("G28 X")
  
    def home_y_button_clicked(self):
        self.send_line("G28 Y")

def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':      
    main()