# coding=utf-8
from PyQt4 import QtGui
from PyQt4.QtCore import QSettings
from serial.tools import list_ports


class QDataRadioButton(QtGui.QRadioButton):
    __data = None

    def setData(self, data):
        self.__data = data

    def data(self):
        return self.__data


class SerialPortDialog(QtGui.QDialog):
    serialport_combobox = None
    settings = None

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.setWindowTitle('Seriellen Port wählen')
        self.setWindowIcon(QtGui.QIcon(':/icons/glyph-router'))

        label = QtGui.QLabel("Port wählen:")

        self.serialport_buttongroup = QtGui.QButtonGroup()

        self.serialport_combobox = QtGui.QComboBox()

        radiobutton_layout = QtGui.QVBoxLayout()

        buttonbox = QtGui.QDialogButtonBox(self)
        buttonbox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Close)

        layout = QtGui.QVBoxLayout()
        layout.addLayout(radiobutton_layout)
        layout.addWidget(buttonbox)

        self.setLayout(layout)
        buttonbox.rejected.connect(self.reject)
        buttonbox.accepted.connect(self.accept)

        self.settings = QSettings('olle-orks.org', 'Bodenpython')

        comports = list_ports.comports()
        self.serialport_combobox.clear()
        idx = 0
        for port in comports:
            curr_rb = QDataRadioButton(port[1])
            curr_rb.setData(port[0])
            radiobutton_layout.addWidget(curr_rb)
            self.serialport_buttongroup.addButton(curr_rb)

            if port[0] == self.settings.value('last_selected_com_port'):
                curr_rb.setChecked(True)

            idx += 1

    def accept(self):
        self.settings.setValue('last_selected_com_port', self.get_selected_serial_port())
        super(SerialPortDialog, self).accept()

    def get_selected_serial_port(self):
        return self.serialport_buttongroup.checkedButton().data()
