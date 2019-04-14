from enum import Enum
import pynmea2
import signal
import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtSerialPort import QSerialPort
import astropy.coordinates as coord
from astropy.time import Time
import astropy.units as u


class State(Enum):
    INITIAL = 0
    HOMING = 1
    HOMED = 2
    TRACKING = 3
    MANUAL = 4


class StateMachine:
    def __init__(self, state_label, qgrbl_terminal, qgps_info, grbl_state_label):
        self.state_label = state_label
        self.qgrbl_terminal = qgrbl_terminal
        self.qgrbl_terminal.state_machine = self
        self.qgps_info = qgps_info
        self.grbl_state_label = grbl_state_label
        self.setState(State.INITIAL)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

    def setState(self, state):
        self.state = state
        self.state_label.setText(str(self.state))

    def gotLine(self, line):
        if self.state == State.INITIAL:
            if line == "[MSG:'$H'|'$X' to unlock]":
                self.setState(State.HOMING)
                self.qgrbl_terminal.send_line("$H")
        elif self.state == State.HOMING and line == 'ok':
            self.setState(State.TRACKING)
        elif self.state == State.TRACKING and line.startswith("<"):
            self.grbl_state_label.setText(line)

    def tick(self):
        if self.state == State.TRACKING:
            az = self.qgps_info.altaz_az_value.text()
            alt = self.qgps_info.altaz_alt_value.text()
            if az == '' or alt == '':
                print("No valid az or alt")
            try:
                xaz = - (90+float(az))
                xalt = -(90-float(alt))
            except ValueError:
                print("No valid az or alt")
            else:
                cmd = "G0 X%.3f" % xaz
                self.qgrbl_terminal.send_line(cmd)
                cmd = "G0 Y%.3f" % xalt
                self.qgrbl_terminal.send_line(cmd)
                cmd = "?"
                self.qgrbl_terminal.send_line(cmd)
        
class QGrblTerminal(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(QtWidgets.QWidget, self).__init__(*args, **kwargs)

        self.serial = QSerialPort()
        port = "/dev/grblserial"
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

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.text)
        
        self.input = QtWidgets.QLineEdit()
        self.input.setMinimumWidth(500)
        self.input.returnPressed.connect(self.line_entered)
        self.layout.addWidget(self.input)

        self.buffer = None
        self.state_machine = None
    
    def line_entered(self):
        self.send_line(self.input.text())
        
    def send_line(self, line):
        self.text.appendPlainText("Sent: " + line)
        b = bytearray(line + '\r', 'utf-8')
        self.serial.writeData(b)
        
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
                if self.state_machine:
                    self.state_machine.gotLine(line)
            else:
                self.buffer = line

def getSunPos(latitude, longitude, t):
    loc = coord.EarthLocation(lon=longitude * u.deg,
                              lat=latitude * u.deg)
    now = Time(t)
    altaz = coord.AltAz(location=loc, obstime=now)
    sun = coord.get_sun(now)
    result = sun.transform_to(altaz)
    return result

class QGPSInfo(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(QtWidgets.QWidget, self).__init__(*args, **kwargs)

        self.serial = QSerialPort()
        port = "/dev/gpsserial"
        self.serial.setPortName(port)
        if self.serial.open(QtCore.QIODevice.ReadWrite):
            self.serial.setDataTerminalReady(True)
            self.serial.setBaudRate(4800)
            self.serial.readyRead.connect(self.on_serial_read)

        self.layout = QtWidgets.QVBoxLayout(self)

        self.latlon_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.latlon_layout)
        self.altaz_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.altaz_layout)

        f = QtGui.QFont(self.font())
        f.setPointSize(36)

        self.latlon_lat_label = QtWidgets.QLabel(self)
        self.latlon_lat_label.setText('lat')
        self.latlon_lat_label.setFont(f)
        self.latlon_layout.addWidget(self.latlon_lat_label)

        self.latlon_lat_value = QtWidgets.QLabel(self)
        self.latlon_lat_value.setFont(f)
        self.latlon_layout.addWidget(self.latlon_lat_value)

        self.latlon_lon_label = QtWidgets.QLabel(self)
        self.latlon_lon_label.setText('lon')
        self.latlon_lon_label.setFont(f)
        self.latlon_layout.addWidget(self.latlon_lon_label)

        self.latlon_lon_value = QtWidgets.QLabel(self)
        self.latlon_lon_value.setFont(f)
        self.latlon_layout.addWidget(self.latlon_lon_value)

        self.latlon_timestamp_label = QtWidgets.QLabel(self)
        self.latlon_timestamp_label.setText('ts')
        self.latlon_timestamp_label.setFont(f)
        self.latlon_layout.addWidget(self.latlon_timestamp_label)

        self.latlon_timestamp_value = QtWidgets.QLabel(self)
        self.latlon_timestamp_value.setFont(f)
        self.latlon_layout.addWidget(self.latlon_timestamp_value)

        self.altaz_alt_label = QtWidgets.QLabel(self)
        self.altaz_alt_label.setText('alt')
        self.altaz_alt_label.setFont(f)
        self.altaz_layout.addWidget(self.altaz_alt_label)

        self.altaz_alt_value = QtWidgets.QLabel(self)
        self.altaz_alt_value.setFont(f)
        self.altaz_layout.addWidget(self.altaz_alt_value)

        self.altaz_az_label = QtWidgets.QLabel(self)
        self.altaz_az_label.setText('az')
        self.altaz_az_label.setFont(f)
        self.altaz_layout.addWidget(self.altaz_az_label)

        self.altaz_az_value = QtWidgets.QLabel(self)
        self.altaz_az_value.setFont(f)
        self.altaz_layout.addWidget(self.altaz_az_value)

    def on_serial_read(self, *args):
        if self.serial.canReadLine():
            line = self.serial.readLine()
            decoded = line.data().decode('US_ASCII')
            msg = pynmea2.parse(decoded)
            if (msg.sentence_type == 'RMC'):
                self.latlon_lat_value.setText("%8.3f" % msg.latitude)
                self.latlon_lon_value.setText("%8.3f" % msg.longitude)
                self.latlon_timestamp_value.setText("%s" % (msg.datetime))
                result = getSunPos(msg.latitude, msg.longitude, msg.datetime)
                self.altaz_alt_value.setText("%8.3f" % result.alt.degree)
                self.altaz_az_value.setText("%8.3f" % result.az.degree)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.state_label = QtWidgets.QLabel(self)
        self.grbl_state_label = QtWidgets.QLabel(self)
        self.qgps_info = QGPSInfo(self)
        self.qgrbl_terminal = QGrblTerminal(self)
        self.state_machine = StateMachine(self.state_label, self.qgrbl_terminal, self.qgps_info, self.grbl_state_label)

        self.main_widget = QtWidgets.QWidget(self)
        self.main_layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.main_layout.addWidget(self.qgps_info)
        self.main_layout.addWidget(self.qgrbl_terminal)
        self.main_layout.addWidget(self.state_label)
        self.main_layout.addWidget(self.grbl_state_label)

        self.setCentralWidget(self.main_widget)

        
        
        
class QApplication(QtWidgets.QApplication):
    def __init__(self, *args, **kwargs):
        super(QApplication, self).__init__(*args, **kwargs)
        self.main_window = MainWindow()
        self.main_window.show()
        

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    app.exec_()
