import sys
import serial
import glob
import os.path
import yaml
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import uic

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

# global settings
np.set_printoptions(precision=4)

# global variables
board_addresses = ["0x40", "0x60", "0x41"]

# helper function to list serial ports
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

# matplotlib canvas
class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

# plot dialog
class PlotDialog(QDialog, MplCanvas):

    def __init__(self, mp_canvas):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(mp_canvas)
        self.setLayout(layout)

# main window class
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("calibration_gui.ui", self)

        # calibration variables
        self.model = np.array([])

        # setup default serial interface
        self.serial_interface = serial.Serial()
        self.serial_interface.timeout = 0.01

        # get available ports and add to combo box menu
        self.port_select.addItems(serial_ports())

        # initialize default gui settings
        self.servo_freq_value.setEnabled(False)
        self.board_address_edit.setEnabled(False)
        self.board_address_edit.setText(board_addresses[self.board_value.value()])
        self.pulse_value.setKeyboardTracking(False) # don't emit value changes while typing
        self.osc_freq_value.setKeyboardTracking(False) # don't emit value changes while typing

        # serial port read timer
        self.read_timer = QTimer()
        self.read_timer.setInterval(100)
        self.read_timer.timeout.connect(self.recurring_serial_read)
        self.read_timer.start()

        # connect slots and signals
        self.start_button.clicked.connect(self.start_clicked)
        self.pulse_value.valueChanged.connect(self.pulse_value_change)
        self.pulse_value.lineEdit().returnPressed.connect(self.add_row_pwm)
        self.board_value.valueChanged.connect(self.board_value_change)
        self.osc_freq_value.valueChanged.connect(self.osc_freq_value_change)
        self.osc_freq_value.lineEdit().returnPressed.connect(self.add_row_osc)
        self.calibrate_button.clicked.connect(self.calibrate_button_clicked)
        self.clear_button.clicked.connect(self.clear_button_clicked)
        self.x_edit.editingFinished.connect(self.evaluate_y)
        self.y_edit.editingFinished.connect(self.evaluate_x)
        self.save_model_button.clicked.connect(self.save_model_clicked)
        self.delete_button.clicked.connect(self.delete_button_clicked)

    def start_clicked(self):
        self.serial_interface.port = self.port_select.currentText()
        if not self.serial_interface.is_open:
            self.serial_interface.baudrate = int(self.baud_select.currentText())
            self.serial_interface.open()
            self.start_button.setText("Stop")
        else:
            self.serial_interface.close()
            self.start_button.setText("Start")

    def recurring_serial_read(self):
        if self.serial_interface.is_open:
            lines = self.serial_interface.readlines()
            for line in lines:
                self.console.insertPlainText(line.decode())
                self.console.ensureCursorVisible()

    def board_value_change(self):
        self.board_address_edit.setText(board_addresses[self.board_value.value()])

    def osc_freq_value_change(self):
        board = self.board_value.value()
        freq = self.osc_freq_value.value()
        if self.serial_interface.is_open:
            # opcode 0x00 sets oscillator frequency
            command = "0 " + str(board) + " " + str(freq) + "\r"
            self.serial_interface.write(command.encode())

    def pulse_value_change(self):
        pulse = self.pulse_value.value()
        board = self.board_value.value()
        servo = self.servo_value.value()
        if self.serial_interface.is_open:
            if self.hold_enable.isChecked():
                # opcode 0x02 sets and holds servo position
                command = "2 " + str(board) + " " + str(servo) + " " + str(pulse) + "\r"
            else:
                # opcode 0x01 sets and releases servo position
                command = "1 " + str(board) + " " + str(servo) + " " + str(pulse) + "\r"
            self.serial_interface.write(command.encode())

    def add_row_osc(self):
        self.add_row(self.osc_freq_value.value())

    def add_row_pwm(self):
        self.add_row(self.pulse_value.value())

    def add_row(self, x):
        val, ok = QInputDialog.getText(self, 'Add measurement', 'Enter measured value for x=' + str(x))
        if ok:
            nrows = self.calibration_table.rowCount()
            self.calibration_table.insertRow(nrows)
            self.calibration_table.setItem(nrows, 0, QTableWidgetItem(str(x)))
            self.calibration_table.setItem(nrows, 1, QTableWidgetItem(val))
        
    def clear_button_clicked(self):
        self.calibration_table.setRowCount(0)

    def delete_button_clicked(self):
        indices = self.calibration_table.selectionModel().selectedRows()
        for index in reversed(sorted(indices)):
            self.calibration_table.removeRow(index.row())
        
    def calibrate_button_clicked(self):
        nrows = self.calibration_table.rowCount()
        x = np.array([])
        y = np.array([])
        try:
            for i in range(nrows):
                x = np.append(x, float(self.calibration_table.item(i, 0).text()))
                y = np.append(y, float(self.calibration_table.item(i, 1).text()))
            
            # calculate fit
            self.model, res, _, _, _ = np.polyfit(x, y, 1, full=True)
            self.coefficients_label.setText(str(self.model))
            self.residuals_label.setText(str(res))
            self.input_limits = np.array([x.min(), x.max()])

            # Create the maptlotlib FigureCanvas object,
            # which defines a single set of axes as self.axes.
            sc = MplCanvas(self, width=5, height=4, dpi=100)

            # plot data
            xn = np.linspace(x.min(),x.max(),100)
            yn = np.poly1d(self.model)
            sc.axes.plot(xn,yn(xn),x,y,'o')

            # create dialog and add canvas widget
            plot_dlg = PlotDialog(sc)
            plot_dlg.exec()
            
        except Exception as error:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Error")
            dlg.setText(type(error).__name__ + ": " + str(error))
            dlg.exec()

    def evaluate_x(self):
        try:
            y = float(self.y_edit.text())
            x = (y - self.model[1]) / self.model[0]
            self.x_edit.setText("{:.4f}".format(x))
        except Exception as error:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Error")
            dlg.setText(type(error).__name__ + ": " + str(error))
            dlg.exec()

    def evaluate_y(self):
        try:
            x = float(self.x_edit.text())
            y = self.model[0] * x + self.model[1]
            self.y_edit.setText("{:.4f}".format(y))
        except Exception as error:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Error")
            dlg.setText(type(error).__name__ + ": " + str(error))
            dlg.exec()

    def save_model_clicked(self):
        try:
            if self.model.size == 0:
                raise ValueError("Nothing to save.")
            save_dlg = QFileDialog(self, directory="../config")
            save_dlg.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            save_dlg.setDefaultSuffix("yaml")
            save_dlg.setOption(QFileDialog.Option.DontConfirmOverwrite)
            save_dlg.setLabelText(QFileDialog.DialogLabel.Accept, "Save/Append")
            #save_dlg.currentChanged.connect(lambda f: save_dlg.setLabelText(QFileDialog.DialogLabel.Accept, "Append") if os.path.isfile(f) else save_dlg.setLabelText(QFileDialog.DialogLabel.Accept, "Save"))
            save_dlg.exec()
            filepath = save_dlg.selectedFiles()[0]
            item_base_name = "servo" # only servo config files are supported at the moment
            item_index = -1
            item_dict = {}
            # open and load config file
            if os.path.isfile(filepath):
                with open(filepath,'r') as file:
                    item_dict = yaml.load(file, Loader=yaml.FullLoader)
                    item_base_name, item_index = list(item_dict)[-1].split("_")
                    if item_base_name != "servo":
                        raise TypeError("Currently only items of type 'servo' are supported!")
            # create the new item
            item_name = item_base_name + "_" + str(int(item_index) + 1)
            item_dict[item_name] = {"board_id": self.board_value.value(),
                                    "osc_frequency": self.osc_freq_value.value(),
                                    "servo_frequency": self.servo_freq_value.value(),
                                    "channel": self.servo_value.value(),
                                    "coefficients": self.model.tolist(),
                                    "input_limits": self.input_limits.tolist()}
            with open(filepath, 'w') as file:
                yaml.dump(item_dict, file)
        except Exception as error:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Error")
            dlg.setText(type(error).__name__ + ": " + str(error))
            dlg.exec()

app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()