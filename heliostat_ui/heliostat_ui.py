from PyQt5 import QtWidgets, QtCore, uic
import sys 
import os
from grblesp32_qobject import GRBLESP32Client
from gps_qobject import GPSQObject
from sun_pos import getSunPos
import pynmea2

STATE_INIT=0
STATE_HOMED_X=1
STATE_HOMED_Y=2
STATE_SET_WORK=3
STATE_READY=4
STATE_SENDING_COMMAND=5
STATE_ERROR=-1

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

        self.grblesp32 = GRBLESP32Client()
        self.grblesp32.messageSignal.connect(self.on_ramps_read)

        self.gps_qobject = GPSQObject()

        self.ramps_input.returnPressed.connect(self.line_entered)

        self.gps_qobject.messageSignal.connect(self.on_gps_read)

        self.state = STATE_INIT
        self.send_line("$HX")

    def line_entered(self):
        line = self.ramps_input.text()
        self.send_line(line)
        self.ramps_input.clear()

    def send_line(self, line):
        self.ramps_output.insertPlainText("Sent: " + line)
        self.ramps_output.insertPlainText("\n")
        self.grblesp32.send_line(line)

    def on_ramps_read(self, data):
        d = data.strip()
        if self.state == STATE_INIT:
            print("in STATE_INIT, got", d)
            if d == 'ok':
                print("got ok")
                self.state = STATE_HOMED_X
                self.send_line("$HY")
            else:
                print("got unexpected data:", d)
                self.state = STATE_ERROR
        elif self.state == STATE_HOMED_X:
            print("in STATE_HOMED_X, got", d)
            if d == 'ok':
                print("got ok")
                self.state = STATE_HOMED_Y
                self.send_line("G10 L20 P1 X0 Y0")
            else:
                print("got unexpected data:", d)
                self.state = STATE_ERROR
        elif self.state == STATE_HOMED_Y:
            print("in STATE_HOMED_X, got", d)
            if d == 'ok':
                print("got ok")
                self.state = STATE_READY
            else:
                print("got unexpected data:", d)
                self.state = STATE_ERROR    
        elif self.state == STATE_SENDING_COMMAND:
            print("in STATE_SENDING_COMMAND, got", d)
            if d == 'ok':
                print("got ok")
                self.state = STATE_READY
            else:
                print("got unexpected data:", d)
                self.state = STATE_ERROR  
        self.ramps_output.insertPlainText(data)
        self.ramps_output.verticalScrollBar().setValue(self.ramps_output.verticalScrollBar().maximum())


    def on_gps_read(self, data):
        try:
            msg = pynmea2.parse(data)
        except pynmea2.ParseError:
            print("failed to parse")
        else:
            if (msg.sentence_type == 'RMC'):
                result = getSunPos(msg.latitude, msg.longitude, msg.datetime)
                self.gps_location.setText(f"{msg.latitude:.2f} {msg.longitude:.2f}")
                self.gps_time.setText(str(msg.datetime))
                self.sun_position.setText(f"Alt: {result.alt.degree:.2f} Az: {result.az.degree:.2f}")
                
                xaz = result.az.degree
                xalt = (90-result.alt.degree)
                if self.state == STATE_READY:
                    cmd = "G0 X%.3f Y%.3f\r\n" % (xaz, xalt)
                    print(cmd)
                    self.state = STATE_SENDING_COMMAND
                    self.send_line(cmd)

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