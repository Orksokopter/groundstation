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

        self.serialport_combobox = QtGui.QComboBox()
        self.serialport_combobox.setEditable(True)

        buttonbox = QtGui.QDialogButtonBox(self)
        buttonbox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Close)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.serialport_combobox)
        layout.addWidget(buttonbox)

        self.setLayout(layout)
        buttonbox.rejected.connect(self.reject)
        buttonbox.accepted.connect(self.accept)

        self.settings = QSettings('olle-orks.org', 'Bodenpython')

        comports = list_ports.comports()
        if comports:
            idx = 0
            for port in comports:
                self.serialport_combobox.addItem(port[1], port[0])

                if port[0] == self.settings.value('last_selected_com_port'):
                    index = self.serialport_combobox.count() - 1
                    self.serialport_combobox.setCurrentIndex(index)

                idx += 1
        else:
            if self.settings.value('last_selected_com_port'):
                self.serialport_combobox.addItem(self.settings.value('last_selected_com_port'))

    def accept(self):
        self.settings.setValue('last_selected_com_port', self.get_selected_serial_port())
        super(SerialPortDialog, self).accept()

    def get_selected_serial_port(self):
        selected_item_data = self.serialport_combobox.itemData(self.serialport_combobox.currentIndex())

        if selected_item_data:
            return selected_item_data
        else:
            return self.serialport_combobox.currentText()
