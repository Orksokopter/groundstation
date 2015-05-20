# coding=utf-8
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QSettings
from serial.tools import list_ports
import sys
import os


class QDataRadioButton(QtWidgets.QRadioButton):
    __data = None

    def setData(self, data):
        self.__data = data

    def data(self):
        return self.__data


class SerialPortDialog(QtWidgets.QDialog):
    serialport_combobox = None
    settings = None

    DARWIN_SERIAL_PORT_PATH = "/dev/tty.Orksokopter-DevB"

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)

        self.setWindowTitle('Seriellen Port wählen')
        self.setWindowIcon(QtGui.QIcon(':/icons/glyph-router'))

        self.serialport_combobox = QtWidgets.QComboBox()
        self.serialport_combobox.setEditable(True)

        buttonbox = QtWidgets.QDialogButtonBox(self)
        buttonbox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Close)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.serialport_combobox)
        layout.addWidget(buttonbox)

        self.setLayout(layout)
        buttonbox.rejected.connect(self.reject)
        buttonbox.accepted.connect(self.accept)

        self.settings = QSettings('olle-orks.org', 'Bodenpython')

        comports = list_ports.comports()

        if sys.platform.lower() == "darwin":
            if os.path.exists(self.DARWIN_SERIAL_PORT_PATH):
                comports.append((self.DARWIN_SERIAL_PORT_PATH, "Orksokopter-DevB"))

        if comports:
            for port in comports:
                self.serialport_combobox.addItem(port[1], port[0])

            if self.settings.value('last_selected_com_port'):
            index = self.serialport_combobox.findData(
                self.settings.value('last_selected_com_port')
            )

            if index != -1:
                self.serialport_combobox.setCurrentIndex(index)

    def accept(self):
        self.settings.setValue('last_selected_com_port', self.get_selected_serial_port())
        super(SerialPortDialog, self).accept()

    def get_selected_serial_port(self):
        selected_item_data = self.serialport_combobox.itemData(self.serialport_combobox.currentIndex())

        if selected_item_data:
            return selected_item_data
        else:
            return self.serialport_combobox.currentText()
