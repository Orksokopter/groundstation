# coding=utf-8
from PyQt4 import QtGui
from PyQt4.QtCore import QSettings
from serial.tools import list_ports

class SerialPortDialog(QtGui.QDialog):
    serialport_combobox = None
    settings = None

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.setWindowTitle('Seriellen Port wählen')
        self.setWindowIcon(QtGui.QIcon(':/icons/glyph-router'))

        label = QtGui.QLabel("Port wählen:")

        self.serialport_combobox = QtGui.QComboBox()

        combolayout = QtGui.QHBoxLayout()
        combolayout.addWidget(label)
        combolayout.addStretch()
        combolayout.addWidget(self.serialport_combobox)

        buttonbox = QtGui.QDialogButtonBox(self)
        buttonbox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Close)

        layout = QtGui.QVBoxLayout()
        layout.addLayout(combolayout)
        layout.addWidget(buttonbox)

        self.setLayout(layout)
        buttonbox.rejected.connect(self.reject)
        buttonbox.accepted.connect(self.accept)

        self.settings = QSettings('olle-orks.org', 'Bodenpython')

        comports = list_ports.comports()
        self.serialport_combobox.clear()
        idx = 0
        for port in comports:
            self.serialport_combobox.addItem(port[1], port[0])

            if port[0] == self.settings.value('last_selected_com_port'):
                self.serialport_combobox.setCurrentIndex(idx)

            idx += 1
        self.serialport_combobox.setFixedWidth(300)

    def accept(self):
        self.settings.setValue('last_selected_com_port', self.get_selected_serial_port())
        super(SerialPortDialog, self).accept()

    def get_selected_serial_port(self):
        return self.serialport_combobox.itemData(self.serialport_combobox.currentIndex())
