import sys

from PyQt5 import QtCore, QtWebSockets, QtNetwork
from PyQt5.QtCore import QUrl, QCoreApplication, QTimer

HOSTNAME="grblesp.local"

class GRBLESP32Client(QtCore.QObject):
    messageSignal = QtCore.pyqtSignal(str)
    def __init__(self):
        super().__init__()

        self.client =  QtWebSockets.QWebSocket("",QtWebSockets.QWebSocketProtocol.Version13,None)
        self.client.error.connect(self.error)
        self.client.connected.connect(self.connected)

        self.client.open(QUrl(f"ws://{HOSTNAME}:81"))
        self.client.pong.connect(self.onPong)
        self.client.textMessageReceived.connect(self.onText)
        self.client.binaryMessageReceived.connect(self.onBinary)

        self.request = QtNetwork.QNetworkRequest()
        url = QtCore.QUrl(f"http://{HOSTNAME}/command?commandText=?")
        self.request.setUrl(url)
        self.manager = QtNetwork.QNetworkAccessManager()

    def connected(self):
        print("connected")
        #self.ping_timer = QtCore.QTimer()
        #self.ping_timer.timeout.connect(self.do_ping)
        #self.ping_timer.start(5000)

        #self.status_timer = QtCore.QTimer()
        #self.status_timer.timeout.connect(self.do_status)
        #self.status_timer.start(1000)

    def onText(self, message):
        if message.startswith("CURRENT_ID"):
            self.current_id = message.split(':')[1]
            print("Current id is:", self.current_id)
        elif message.startswith("ACTIVE_ID"):
            active_id = message.split(':')[1]
            if self.current_id != active_id:
                print("Warning: different active id.")
        elif message.startswith("PING"):
            ping_id = message.split(":")[1]
            if ping_id != self.current_id:
                print("Warning: ping different active id.")

    def onBinary(self, message):
        print("onBinary: message", message)
        self.messageSignal.emit(str(message, 'ascii'))
        
    def do_ping(self):
        pass
        #self.client.ping(b"0")

    def do_status(self):        
        self.replyObject = self.manager.get(self.request)


    def send_line(self, line):
        print("client: send_line", line)
        request = QtNetwork.QNetworkRequest()
        url = QtCore.QUrl(f"http://{HOSTNAME}/command?commandText={line}")
        request.setUrl(url)
        self.manager.get(request)

    def onPong(self, elapsedTime, payload):
        print("onPong - time: {} ; payload: {}".format(elapsedTime, payload))

    def error(self, error_code):
        print("error code: {}".format(error_code))
        if error_code == 1:
            print(self.client.errorString())

    def close(self):
        self.client.close()

    def ping(self):
        self.client.do_ping()


if __name__ == '__main__':
    app = QCoreApplication(sys.argv)

    client = GRBLESP32Client()

    app.exec_()