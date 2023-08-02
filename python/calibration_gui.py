import sys
import serial
import glob

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import uic

def serial_ports():
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("mainwindow.ui", self)

        self.serial_interface = serial.Serial()
        self.serial_interface.timeout = 0.01

        self.port_select.addItems(serial_ports())

        self.start_button.clicked.connect(self.start_clicked)

        self.read_timer = QTimer()
        self.read_timer.setInterval(100)
        self.read_timer.timeout.connect(self.recurring_serial_read)
        self.read_timer.start()

        self.pulse_slider.valueChanged.connect(self.pulse_slider_change)

    def start_clicked(self):
        self.serial_interface.port = self.port_select.currentText()
        if not self.serial_interface.is_open:
            self.serial_interface.open()

    def recurring_serial_read(self):
        if self.serial_interface.is_open:
            lines = self.serial_interface.readlines()
            for line in lines:
                self.console.insertPlainText(line.decode())
                self.console.ensureCursorVisible()

    def pulse_slider_change(self):
        pulse = self.pulse_slider.value()
        self.pulse_edit.setText(str(pulse))
        if self.serial_interface.is_open:
            command = "1 0 4 " + str(pulse) + "\r\n"
            self.serial_interface.write(command.encode())


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()