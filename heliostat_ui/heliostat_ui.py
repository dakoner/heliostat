from PyQt5 import QtWidgets, uic
import sys 
import os

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

    def down_button_clicked(self):
        pass
    
    def up_button_clicked(self):
        pass

    def right_button_clicked(self):
        pass
    
    def left_button_clicked(self):
        pass
  
    def home_x_button_clicked(self):
        pass
  
    def home_y_button_clicked(self):
        pass

def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':      
    main()