from enum import Enum
import pynmea2
import PySpin
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



class PySpinCamera:
    def __init__(self):
        # Retrieve singleton reference to system object
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()
        num_cameras = self.cam_list.GetSize()
        print('Number of cameras detected: %d' % num_cameras)
        if num_cameras == 0:
            self.cam_list.Clear()
            self.system.ReleaseInstance()
            raise RuntimeError("Not enough cameras")

        self.cam = self.cam_list[0]
        self.nodemap_tldevice = self.cam.GetTLDeviceNodeMap()
        self.cam.Init()
        self.nodemap = self.cam.GetNodeMap()
        
    def enter_acquisition_mode(self):
        node_acquisition_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode('AcquisitionMode'))
        if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
            print('Unable to set acquisition mode to continuous (enum retrieval). Aborting...')
            return False
        node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
        if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(node_acquisition_mode_continuous):
            print('Unable to set acquisition mode to continuous (entry retrieval). Aborting...')
            return False
        acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()
        node_acquisition_mode.SetIntValue(acquisition_mode_continuous)
        print('Acquisition mode set to continuous...')
        self.cam.BeginAcquisition()

    def acquire_image(self):
        image_result = self.cam.GetNextImage()
        if image_result.IsIncomplete():
            print('Image incomplete with image status %d ...' % image_result.GetImageStatus())
        else:
            width = image_result.GetWidth()
            height = image_result.GetHeight()
            stride = image_result.GetStride()
            d = image_result.GetData()
            image = QtGui.QImage(d, width, height, stride, QtGui.QImage.Format_Indexed8)
            # image = image.scaledToHeight(512)
            return image

    def leave_acquisition_mode(self):
        self.cam.EndAcquisition()

    def __del__(self):
        self.reset_exposure()
        self.cam.DeInit()
        del self.cam
        self.cam_list.Clear()
        self.system.ReleaseInstance()


    def configure_exposure(self, value):
        try:
            result = True
            # Turn off automatic exposure mode
            if self.cam.ExposureAuto.GetAccessMode() != PySpin.RW:
                print('Unable to disable automatic exposure. Aborting...')
                return False

            self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
            print('Automatic exposure disabled...')

            # Set exposure time manually; exposure time recorded in microseconds
            if self.cam.ExposureTime.GetAccessMode() != PySpin.RW:
                print('Unable to set exposure time. Aborting...')
                return False

            # Ensure desired exposure time does not exceed the maximum
            exposure_time_to_set = value
            exposure_time_to_set = min(self.cam.ExposureTime.GetMax(), exposure_time_to_set)
            self.cam.ExposureTime.SetValue(exposure_time_to_set)

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            result = False

        return result

    def reset_exposure(self):
        """
        This function returns the camera to a normal state by re-enabling automatic exposure.

        :return: True if successful, False otherwise.
        :rtype: bool
        """
        try:
            result = True

            # Turn automatic exposure back on
            #
            # *** NOTES ***
            # Automatic exposure is turned on in order to return the camera to its
            # default state.

            if self.cam.ExposureAuto.GetAccessMode() != PySpin.RW:
                print('Unable to enable automatic exposure (node retrieval). Non-fatal error...')
                return False

            self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Continuous)

            print('Automatic exposure enabled...')

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            result = False

        return result


class SpinWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(SpinWidget, self).__init__(*args, **kwargs)

        self.layout = QtWidgets.QVBoxLayout(self)

        self.label = QtWidgets.QLabel()
        self.layout.addWidget(self.label)

        self.camera = PySpinCamera()
        self.camera.enter_acquisition_mode()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.camera_callback)
        self.timer.start(0) 
        
        self.sp = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sp.valueChanged.connect(self.exposure_change)
        self.sp.setMinimum(0)
        self.sp.setMaximum(50000)
        self.sp.setValue(0)
        self.sp.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.sp.setTickInterval(5000)
        self.layout.addWidget(self.sp)

    def exposure_change(self, value):
        if value == 0:
            print("enable auto")
            self.camera.reset_exposure()
        else:
            print('set exposure time to', value)
            self.camera.configure_exposure(value)
        return True

    def camera_callback(self):
        image = self.camera.acquire_image()
        pixmap = QtGui.QPixmap.fromImage(image)
        self.label.setPixmap(pixmap.scaledToHeight(512))


class StateMachine:
    def __init__(self, state_label, qgrbl_terminal, qgps_info):
        self.state_label = state_label
        self.qgrbl_terminal = qgrbl_terminal
        self.qgrbl_terminal.state_machine = self
        self.qgps_info = qgps_info
        self.setState(State.INITIAL)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

    def setState(self, state):
        self.state = state
        self.state_label.setText(self.state.name)

    def gotLine(self, line):
        if line.startswith("<"):
            s = line[1:-1].split("|")
            state = s[0]
            mpos = s[1]
            ps = mpos.split(":")
            xpos, ypos, zpos = ps[1].split(",")
            sw = s[2]
            self.qgrbl_terminal.state_label.setText(state)
            self.qgrbl_terminal.pos_x_value.setText(xpos)
            self.qgrbl_terminal.pos_y_value.setText(ypos)

        if self.state == State.INITIAL:
            pass
            # if line == "[MSG:'$H'|'$X' to unlock]":
            #     self.setState(State.HOMING)
            #     self.qgrbl_terminal.send_line("$H")
        elif self.state == State.HOMING and line == 'ok':
            self.setState(State.HOMED)

    def tick(self):
        if self.state != State.HOMING and self.state != State.INITIAL:
            cmd = "?"
            self.qgrbl_terminal.send_line(cmd)
        if self.state == State.TRACKING:
            az = self.qgps_info.altaz_az_value.text()
            alt = self.qgps_info.altaz_alt_value.text()
            if az == '' or alt == '':
                print("No valid az or alt")
            try:
                pos_x = - (90+float(az))
                pos_y = -(90-float(alt))
            except ValueError:
                print("No valid az or alt")
            else:
                cmd = "G0 X%.3f" % pos_x
                self.qgrbl_terminal.send_line(cmd)
                cmd = "G0 Y%.3f" % pos_y
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


        self.layout = QtWidgets.QVBoxLayout(self)

        f = QtGui.QFont(self.font())
        f.setPointSize(36)

        self.info_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.info_layout)
        
        self.state_label = QtWidgets.QLabel(self)
        self.state_label.setFont(f)
        self.info_layout.addWidget(self.state_label)
        
        self.pos_x_label = QtWidgets.QLabel(self)
        self.pos_x_label.setText('PosX')
        self.pos_x_label.setFont(f)
        self.info_layout.addWidget(self.pos_x_label)

        self.pos_x_value = QtWidgets.QLabel(self)
        self.pos_x_value.setFont(f)
        self.info_layout.addWidget(self.pos_x_value)

        self.pos_y_label = QtWidgets.QLabel(self)
        self.pos_y_label.setText('PosY')
        self.pos_y_label.setFont(f)
        self.info_layout.addWidget(self.pos_y_label)

        self.pos_y_value = QtWidgets.QLabel(self)
        self.pos_y_value.setFont(f)
        self.info_layout.addWidget(self.pos_y_value)

        font = QtGui.QFont("nonexistent")
        font.setStyleHint(QtGui.QFont.Monospace)
        self.text = QtWidgets.QPlainTextEdit()
        self.text.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.text.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.text.setMinimumWidth(500)
        self.text.setMinimumHeight(100)
        self.text.setFont(font)
        self.text.setReadOnly(True)
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
                if msg.latitude != 0.0 and msg.longitude != 0.0:
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
        f = QtGui.QFont(self.font())
        f.setPointSize(36)
        self.state_label.setFont(f)
        self.qgps_info = QGPSInfo(self)
        self.qgrbl_terminal = QGrblTerminal(self)
        self.spin_widget = SpinWidget(self)
        self.state_machine = StateMachine(self.state_label, self.qgrbl_terminal, self.qgps_info)

        self.main_widget = QtWidgets.QWidget(self)
        self.main_layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.main_layout.addWidget(self.qgps_info)
        self.main_layout.addWidget(self.state_label)
        self.main_layout.addWidget(self.qgrbl_terminal)
        self.main_layout.addWidget(self.spin_widget)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.home_button = QtWidgets.QPushButton("Home")
        self.home_button.clicked.connect(self.home_clicked)
        self.button_layout.addWidget(self.home_button)
        self.track_button = QtWidgets.QPushButton("Track")
        self.track_button.clicked.connect(self.track_clicked)
        self.button_layout.addWidget(self.track_button)
        self.up_button = QtWidgets.QPushButton("Up")
        self.up_button.clicked.connect(self.up_clicked)
        self.button_layout.addWidget(self.up_button)
        self.down_button = QtWidgets.QPushButton("Down")
        self.down_button.clicked.connect(self.down_clicked)
        self.button_layout.addWidget(self.down_button)
        self.left_button = QtWidgets.QPushButton("Left")
        self.left_button.clicked.connect(self.left_clicked)
        self.button_layout.addWidget(self.left_button)
        self.right_button = QtWidgets.QPushButton("Right")
        self.right_button.clicked.connect(self.right_clicked)
        self.button_layout.addWidget(self.right_button)
        self.main_layout.addLayout(self.button_layout)
        self.setCentralWidget(self.main_widget)

    def home_clicked(self, *args, **kwargs):
        print("home_clicked")
        self.state_machine.setState(State.HOMING)
        self.qgrbl_terminal.send_line("$H")

    def track_clicked(self, *args, **kwargs):
        print("track_clicked")
        self.state_machine.setState(State.TRACKING)

    def up_clicked(self, *args, **kwargs):
        print("up_clicked")
        self.state_machine.setState(State.MANUAL)
        pos_y = float(self.qgrbl_terminal.pos_y_value.text())
        pos_y += 1
        self.qgrbl_terminal.pos_y_value.setText(str(pos_y))
        cmd = "G0 Y%.3f" % pos_y
        self.qgrbl_terminal.send_line(cmd)
        
    def down_clicked(self, *args, **kwargs):
        print("down_clicked")
        self.state_machine.setState(State.MANUAL)
        pos_y = float(self.qgrbl_terminal.pos_y_value.text())
        pos_y -= 1
        self.qgrbl_terminal.pos_y_value.setText(str(pos_y))
        cmd = "G0 Y%.3f" % pos_y
        self.qgrbl_terminal.send_line(cmd)

    def left_clicked(self, *args, **kwargs):
        print("left_clicked")
        self.state_machine.setState(State.MANUAL)
        pos_x = float(self.qgrbl_terminal.pos_x_value.text())
        pos_x -= 1
        self.qgrbl_terminal.pos_x_value.setText(str(pos_x))
        cmd = "G0 X%.3f" % pos_x
        self.qgrbl_terminal.send_line(cmd)

    def right_clicked(self, *args, **kwargs):
        print("right_clicked")
        self.state_machine.setState(State.MANUAL)
        pos_x = float(self.qgrbl_terminal.pos_x_value.text())
        pos_x += 1
        self.qgrbl_terminal.pos_x_value.setText(str(pos_x))
        cmd = "G0 X%.3f" % pos_x
        self.qgrbl_terminal.send_line(cmd)
        
        
        
class QApplication(QtWidgets.QApplication):
    def __init__(self, *args, **kwargs):
        super(QApplication, self).__init__(*args, **kwargs)
        self.main_window = MainWindow()
        self.main_window.show()
        

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    app.exec_()
