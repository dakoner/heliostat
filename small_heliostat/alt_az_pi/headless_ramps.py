import signal
import time
from PyQt5 import QtCore
from ramps_qobject import QRAMPSObject
from mqtt_qobject import MqttClient

class Tui(QtCore.QObject):

    def __init__(self, app):
        super(Tui, self).__init__()

        self.app = app

        self.ramps = QRAMPSObject()
        self.ramps.messageSignal.connect(self.on_serial_read)
        time.sleep(1.5)
        self.ramps.send_line("G91")
        time.sleep(0.1)
        

        self.client = MqttClient(self)
        self.client.hostname = "localhost"
        self.client.connectToHost()

        self.client.stateChanged.connect(self.on_stateChanged)
        self.client.messageSignal.connect(self.on_messageSignal)
        
    def on_serial_read(self, data):
        self.client.publish("heliostat/ramps/output", data)


    @QtCore.pyqtSlot(int)
    def on_stateChanged(self, state):
        if state == MqttClient.Connected:
            self.client.subscribe("heliostat/ramps/command")

    @QtCore.pyqtSlot(str, str)
    def on_messageSignal(self, topic, payload):
        if topic == 'heliostat/ramps/command':
            self.ramps.send_line(payload)

if __name__ == "__main__":
    import sys
    app = QtCore.QCoreApplication(sys.argv)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    tui = Tui(app)
    sys.exit(app.exec_())

