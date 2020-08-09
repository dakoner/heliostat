#!/usr/bin/python3
import time
import io
import sys
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QWidget, QVBoxLayout, QPushButton, QSizePolicy
from PyQt5.QtCore import Qt, QTimer, QRect, QObject, pyqtSignal, QThread
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import pyqtSlot
import picamera
from mqtt_qobject import MqttClient
from pi_camera_qobject import QPiCamera, RESOLUTION
TIMER_TICK=1



class Window(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(QMainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("My Awesome App")
        self.setFixedSize(*RESOLUTION)

        self.client = MqttClient(self)
        self.client.hostname = "localhost"
        self.client.connectToHost()
                                
        self.label = QLabel(parent=self)
        self.label.show()
        self.qimage = QImage(RESOLUTION[0], RESOLUTION[1], QImage.Format_RGB888)
        self.label.resize(self.qimage.size())

        up_button = QPushButton("Up", parent=self)
        up_button.setAutoRepeat(True)
        up_button.setAutoRepeatInterval(150)
        up_button.move(400, 10)
        up_button.setFixedSize(120,60)
        up_button.show()
        up_button.clicked.connect(self.on_up_button)

        down_button = QPushButton("Down", parent=self)
        down_button.setAutoRepeat(True)
        down_button.setAutoRepeatInterval(150)
        down_button.move(400, 400)
        down_button.setFixedSize(120,60)
        down_button.show()
        down_button.clicked.connect(self.on_down_button)

        left_button = QPushButton("Left", parent=self)
        left_button.setAutoRepeat(True)
        down_button.setAutoRepeatInterval(150)
        left_button.move(10, 240)
        left_button.setFixedSize(120,60)
        left_button.show()
        left_button.clicked.connect(self.on_left_button)

        right_button = QPushButton("Right", parent=self)
        right_button.setAutoRepeat(True)
        right_button.setAutoRepeatInterval(150)
        right_button.move(675, 240)
        right_button.setFixedSize(120,60)
        right_button.show()
        right_button.clicked.connect(self.on_right_button)

        
        self.qpicamera_thread = QThread()
        self.qpicamera = QPiCamera()
        self.qpicamera.messageSignal.connect(self.on_qpicameraSignal)
        self.qpicamera.moveToThread(self.qpicamera_thread)
        self.qpicamera_thread.started.connect(self.qpicamera.loop)
        self.qpicamera_thread.start()

    def on_up_button(self):
        p = self.label.pos()
        self.client.publish("heliostat/ramps/command", "G0 Y1")

    def on_down_button(self):
        p = self.label.pos()
        self.client.publish("heliostat/ramps/command", "G0 Y-1")

    def on_left_button(self):
        p = self.label.pos()
        self.client.publish("heliostat/ramps/command", "G0 X-1")

    def on_right_button(self):
        p = self.label.pos()
        self.client.publish("heliostat/ramps/command", "G0 X1")

    @pyqtSlot(bytes)
    def on_qpicameraSignal(self, img):
        b = self.qimage.bits()
        b.setsize(RESOLUTION[0] * RESOLUTION[1] * 3)
        b[:] = img
        pixmap = QPixmap(self.qimage)
        self.label.setPixmap(pixmap)

def main(): 
    app = QApplication(sys.argv)

    mw = Window()
    mw.show()
    app.exec_()

if __name__ == '__main__':
    main()
